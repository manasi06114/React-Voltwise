import { useState, useEffect, useRef, useCallback } from 'react';
import StatCard from './components/StatCard';
import EnergyChart from './components/EnergyChart';
import BatteryGauge from './components/BatteryGauge';
import RegionPanel from './components/RegionPanel';
import ActionPanel from './components/ActionPanel';
import CarbonTracker from './components/CarbonTracker';
import GridMap from './components/GridMap';
import RenewableForecast from './components/RenewableForecast';
import BlackoutRiskPanel from './components/BlackoutRiskPanel';
import StabilityIndex from './components/StabilityIndex';
import DisasterCreator from './components/DisasterCreator';
import EmergencyRecovery from './components/EmergencyRecovery';
import AIDecisionLog from './components/AIDecisionLog';
import { resetEnv, stepEnv, geminiStep, injectScenario, clearScenario } from './api/gridApi';
import './index.css';

const MAX_HISTORY = 48;

function buildHistoryPoint(obs, info, step) {
  return {
    step,
    demand: obs?.demand ?? 0,
    solar: obs?.solar_generation ?? 0,
    wind: obs?.wind_generation ?? 0,
    battery: obs?.battery_storage ?? 0,
    fossil_fuel: info?.fossil_fuel_used ?? obs?.fossil_fuel_used ?? 0,
  };
}

export default function App() {
  const [task, setTask] = useState('medium');
  const [obs, setObs] = useState(null);
  const [info, setInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [stepCount, setStepCount] = useState(0);
  const [totalReward, setTotalReward] = useState(0);
  const [lastAction, setLastAction] = useState(null);
  const [geminiMode, setGeminiMode] = useState(false);
  const [lastActionSource, setLastActionSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [activeScenario, setActiveScenario] = useState(null);
  const [aiDecisions, setAiDecisions] = useState([]);
  const [error, setError] = useState(null);
  const autoRef = useRef(null);
  const stepCountRef = useRef(0);

  // Keep ref in sync with state
  useEffect(() => { stepCountRef.current = stepCount; }, [stepCount]);

  const handleReset = useCallback(async (selectedTask) => {
    setLoading(true);
    setError(null);
    try {
      const data = await resetEnv(selectedTask ?? task);
      const obsData = data.observation;
      setObs(obsData);
      setInfo(null);
      setHistory([buildHistoryPoint(obsData, null, 0)]);
      setStepCount(0);
      stepCountRef.current = 0;
      setTotalReward(0);
      setLastAction(null);
      setDone(false);
      setActiveScenario(null);
      setAiDecisions([]);
      setGeminiMode(false);
    } catch (err) {
      console.error('Reset failed:', err);
      setError('Backend connection failed. Make sure the server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }, [task]);

  useEffect(() => { handleReset(task); }, []); // eslint-disable-line

  const applyStepData = useCallback((data, action) => {
    const newStep = stepCountRef.current + 1;
    const obsData = data.observation;
    const infoData = data.info || {};

    setObs(obsData);
    setInfo(infoData);
    setTotalReward(r => r + (data.reward ?? 0));
    setStepCount(newStep);
    stepCountRef.current = newStep;
    setDone(!!data.done);
    setLastAction(action ?? data.action ?? null);
    setLastActionSource(data.action_source ?? 'manual');
    setHistory(prev => [
      ...prev.slice(-MAX_HISTORY + 1),
      buildHistoryPoint(obsData, infoData, newStep),
    ]);
    return { step: newStep, reward: data.reward ?? 0, source: data.action_source };
  }, []);

  const handleAction = useCallback(async (action) => {
    if (!obs || done || loading) return;
    setError(null);
    try {
      const data = await stepEnv(task, action);
      applyStepData(data, action);
    } catch (err) {
      console.error('Step failed:', err);
      setError('Step failed. Check backend connection.');
    }
  }, [obs, done, loading, task, applyStepData]);

  const handleGeminiStep = useCallback(async () => {
    if (!obs || done) return;
    try {
      const data = await geminiStep(task);
      const meta = applyStepData(data, data.action);
      setAiDecisions(prev => [...prev.slice(-20), {
        step: meta.step,
        action: data.action,
        reward: meta.reward,
        source: data.action_source?.startsWith('mock') ? 'mock' : 'gemini',
      }]);
    } catch (err) {
      console.error('Gemini step failed:', err);
    }
  }, [obs, done, task, applyStepData]);

  const handleScenarioInject = useCallback(async (scenario, intensity) => {
    setError(null);
    try {
      const data = await injectScenario(task, scenario, intensity);
      if (data.observation) setObs(data.observation);
      setActiveScenario(scenario);
    } catch (err) {
      console.error('Scenario inject failed:', err);
      setError('Failed to inject scenario.');
    }
  }, [task]);

  const handleScenarioClear = useCallback(async () => {
    setError(null);
    try {
      const data = await clearScenario(task);
      if (data.observation) setObs(data.observation);
      setActiveScenario(null);
    } catch (err) {
      console.error('Scenario clear failed:', err);
    }
  }, [task]);

  // AI auto-step interval
  useEffect(() => {
    if (geminiMode && !done) {
      const id = setInterval(() => {
        handleGeminiStep();
      }, 2500);
      autoRef.current = id;
      return () => clearInterval(id);
    }
    return () => { if (autoRef.current) clearInterval(autoRef.current); };
  }, [geminiMode, done, handleGeminiStep]);

  const handleTaskSelect = async (newTask) => {
    setTask(newTask);
    setGeminiMode(false);
    if (autoRef.current) clearInterval(autoRef.current);
    await handleReset(newTask);
  };

  const stability = obs
    ? obs.transmission_load < 90
      ? { label: 'Stable', color: 'status-ok' }
      : obs.transmission_load < 98
      ? { label: 'Warning', color: 'status-warn' }
      : { label: 'Critical', color: 'status-danger' }
    : { label: '---', color: 'status-neutral' };

  const renewable = (obs?.solar_generation ?? 0) + (obs?.wind_generation ?? 0);
  const demandCoverage = obs?.demand ? Math.min(100, (renewable / obs.demand) * 100) : 0;

  return (
    <div className="dashboard-shell">
      <aside className="sidebar panel-animate">
        <div className="sidebar-brand">
          <div className="brand-mark">V</div>
          <div>
            <h1>VoltWise</h1>
            <p>Pune Smart Grid</p>
          </div>
        </div>

        <div className="sidebar-group">
          <h4>Task</h4>
          {['easy', 'medium', 'hard'].map(t => (
            <button
              key={t}
              className={`nav-item ${task === t ? 'nav-item-active' : ''}`}
              onClick={() => handleTaskSelect(t)}
            >
              {t === 'easy' ? 'Single City' : t === 'medium' ? 'Multi Region' : 'Fluctuation'}
            </button>
          ))}
        </div>

        <div className="sidebar-group">
          <h4>AI Control</h4>
          <button
            className={`nav-item ${geminiMode ? 'nav-item-ai-active' : ''}`}
            onClick={() => setGeminiMode(v => !v)}
            disabled={done || !obs}
          >
            {geminiMode ? 'Stop AI Agent' : 'Start AI Agent'}
          </button>
          <button className="nav-item" onClick={() => handleReset(task)} disabled={loading}>
            Reset Episode
          </button>
        </div>

        <div className="sidebar-foot">
          <span className={`status-chip ${stability.color}`}>{stability.label}</span>
          <p>Step {stepCount} | Reward {totalReward.toFixed(1)}</p>
        </div>
      </aside>

      <main className="main-area">
        {/* Error Banner */}
        {error && (
          <div className="inline-alert accent panel-animate" style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.3)', color: '#dc2626' }}>
            <span>{error}</span>
            <button onClick={() => setError(null)} style={{ background: '#ef4444', color: '#fff', border: 0, borderRadius: 8, padding: '6px 10px', cursor: 'pointer' }}>Dismiss</button>
          </div>
        )}

        {/* AI Active Banner */}
        {geminiMode && !done && (
          <div className="ai-banner panel-animate">
            <div className="ai-banner-pulse" />
            <span>
              {lastActionSource?.startsWith('mock')
                ? 'AI Agent (mock fallback) managing Pune grid'
                : 'Gemini AI is managing the Pune power grid'}
            </span>
            {lastAction !== null && <strong>Last action: {lastAction}</strong>}
          </div>
        )}

        {done && (
          <section className="inline-alert success panel-animate">
            <span>Episode complete ({stepCount} steps, reward: {totalReward.toFixed(1)})</span>
            <button onClick={() => handleReset(task)}>New Episode</button>
          </section>
        )}

        {activeScenario && (
          <section className="inline-alert accent panel-animate">
            <span>Active disaster: <strong>{activeScenario.replace(/_/g, ' ')}</strong></span>
            <button onClick={handleScenarioClear} style={{ background: '#6d5dfc', color: '#fff', border: 0, borderRadius: 8, padding: '6px 10px', cursor: 'pointer', fontWeight: 600, fontSize: 12 }}>Clear</button>
          </section>
        )}

        {/* KPI Cards */}
        <section className="kpi-grid">
          <StatCard title="Total Demand" value={obs?.demand?.toFixed(1) ?? '---'} unit="MW" tone="danger" />
          <StatCard title="Renewable Supply" value={renewable.toFixed(1)} unit="MW" tone="success" />
          <StatCard title="Transmission Load" value={obs?.transmission_load?.toFixed(1) ?? '---'} unit="%" tone="info" />
          <StatCard title="Coverage" value={demandCoverage.toFixed(1)} unit="%" tone="accent" />
        </section>

        {/* PUNE MAP */}
        <section>
          <GridMap task={task} refreshTrigger={stepCount} />
        </section>

        {/* Charts + Carbon */}
        <section className="chart-grid">
          <div className="span-2"><EnergyChart history={history} /></div>
          <CarbonTracker history={history} />
        </section>

        {/* Intelligence Row */}
        <section className="intel-grid">
          <RenewableForecast task={task} refreshTrigger={stepCount} />
          <BlackoutRiskPanel task={task} refreshTrigger={stepCount} />
          <StabilityIndex task={task} refreshTrigger={stepCount} />
        </section>

        {/* Operations Row */}
        <section className="ops-grid-extended">
          <BatteryGauge level={obs?.battery_storage ?? 0} />
          <RegionPanel regionDemands={obs?.region_demands} blackout={info?.blackout ?? obs?.blackout} />
          <ActionPanel onAction={handleAction} disabled={done || loading || !obs} lastAction={lastAction} />
          <DisasterCreator
            onInject={handleScenarioInject}
            onClear={handleScenarioClear}
            activeScenario={activeScenario}
          />
          <EmergencyRecovery task={task} onInject={handleScenarioInject} onClear={handleScenarioClear} />
        </section>

        {/* AI Decision Log */}
        <section>
          <AIDecisionLog decisions={aiDecisions} isActive={geminiMode} />
        </section>
      </main>
    </div>
  );
}
