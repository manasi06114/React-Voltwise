import { useState, useEffect, useRef, useCallback } from 'react';
import StatCard from './components/StatCard';
import EnergyChart from './components/EnergyChart';
import BatteryGauge from './components/BatteryGauge';
import RegionPanel from './components/RegionPanel';
import ActionPanel from './components/ActionPanel';
import ScenarioSimulator from './components/ScenarioSimulator';
import CarbonTracker from './components/CarbonTracker';
import { resetEnv, stepEnv, geminiStep } from './api/gridApi';
import './index.css';

const MAX_HISTORY = 48;

function buildHistoryPoint(obs, info, step) {
  return {
    step,
    demand: obs.demand,
    solar: obs.solar_generation,
    wind: obs.wind_generation,
    battery: obs.battery_storage,
    fossil_fuel: info?.fossil_fuel_used ?? 0,
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
  const [autoRun, setAutoRun] = useState(false);
  const [geminiMode, setGeminiMode] = useState(false);
  const [lastActionSource, setLastActionSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const autoRef = useRef(null);

  const handleReset = useCallback(async (selectedTask) => {
    setLoading(true);
    try {
      const data = await resetEnv(selectedTask ?? task);
      setObs(data.observation);
      setInfo(null);
      setHistory([buildHistoryPoint(data.observation, null, 0)]);
      setStepCount(0);
      setTotalReward(0);
      setLastAction(null);
      setDone(false);
    } catch {
      // backend not running — show mock data so UI is still visible
      const mock = {
        demand: 240, solar_generation: 80, wind_generation: 60,
        battery_storage: 55, grid_capacity: 350, transmission_load: 68,
        time_of_day: 14, region_demands: [100, 80, 60],
      };
      setObs(mock);
      setHistory([buildHistoryPoint(mock, null, 0)]);
    } finally {
      setLoading(false);
    }
  }, [task]);

  useEffect(() => { handleReset(task); }, []); // eslint-disable-line

  const _applyStepData = useCallback((data, action) => {
    const newStep = stepCount + 1;
    setObs(data.observation);
    setInfo(data.info);
    setTotalReward(r => r + (data.reward ?? 0));
    setStepCount(newStep);
    setDone(data.done);
    setLastAction(action ?? data.action ?? null);
    setLastActionSource(data.action_source ?? 'manual');
    setHistory(prev => [
      ...prev.slice(-MAX_HISTORY + 1),
      buildHistoryPoint(data.observation, data.info, newStep),
    ]);
  }, [stepCount]);

  const handleAction = useCallback(async (action) => {
    if (!obs || done) return;
    try {
      const data = await stepEnv(task, action);
      _applyStepData(data, action);
    } catch {
      console.warn('Backend unavailable — action skipped');
    }
  }, [obs, done, task, _applyStepData]);

  const handleGeminiStep = useCallback(async () => {
    if (!obs || done) return;
    try {
      const data = await geminiStep(task);
      _applyStepData(data, data.action);
    } catch {
      console.warn('Gemini step failed');
    }
  }, [obs, done, task, _applyStepData]);

  // Random auto-run: random action every 1.5 s
  useEffect(() => {
    if (autoRun && !geminiMode && !done) {
      autoRef.current = setInterval(() => {
        handleAction(Math.floor(Math.random() * 6));
      }, 1500);
    }
    return () => clearInterval(autoRef.current);
  }, [autoRun, geminiMode, done, handleAction]);

  // Gemini auto-run: Gemini decides every 3 s (API latency buffer)
  useEffect(() => {
    if (geminiMode && !done) {
      autoRef.current = setInterval(() => {
        handleGeminiStep();
      }, 3000);
    }
    return () => clearInterval(autoRef.current);
  }, [geminiMode, done, handleGeminiStep]);

  const handleTaskSelect = async (newTask) => {
    setTask(newTask);
    setAutoRun(false);
    setGeminiMode(false);
    await handleReset(newTask);
  };

  const stability = obs
    ? obs.transmission_load < 90
      ? { label: 'Stable',   color: 'text-emerald-400' }
      : obs.transmission_load < 98
      ? { label: 'Warning',  color: 'text-yellow-400' }
      : { label: 'Critical', color: 'text-red-400' }
    : { label: '—', color: 'text-slate-400' };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/60 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚡</span>
          <div>
            <h1 className="text-lg font-bold text-white leading-none">VoltWise</h1>
            <p className="text-xs text-slate-400">AI Smart Grid Optimizer</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-semibold ${stability.color}`}>{stability.label}</span>
          <span className="text-xs text-slate-500 mr-1">Step {stepCount}</span>

          {/* Gemini AI mode */}
          <button
            onClick={() => { setGeminiMode(v => !v); setAutoRun(false); }}
            disabled={done}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 disabled:opacity-40 ${
              geminiMode
                ? 'bg-violet-700 hover:bg-violet-600 text-white ring-2 ring-violet-400'
                : 'bg-violet-900 hover:bg-violet-800 text-violet-300'
            }`}
          >
            <span>✦</span>
            {geminiMode ? 'Gemini ON' : 'Gemini AI'}
          </button>

          {/* Random auto-run */}
          <button
            onClick={() => { setAutoRun(v => !v); setGeminiMode(false); }}
            disabled={done}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 ${
              autoRun
                ? 'bg-red-700 hover:bg-red-600 text-white'
                : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
            }`}
          >
            {autoRun ? 'Stop' : 'Auto Run'}
          </button>

          <button
            onClick={() => handleReset(task)}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 disabled:opacity-50"
          >
            Reset
          </button>
        </div>
      </header>

      <main className="p-6 space-y-6 max-w-7xl mx-auto">
        {done && (
          <div className="bg-emerald-900/40 border border-emerald-700 rounded-xl px-5 py-3 text-emerald-300 text-sm flex items-center justify-between">
            <span>Episode complete — total reward: <strong>{totalReward.toFixed(2)}</strong></span>
            <button
              onClick={() => handleReset(task)}
              className="bg-emerald-700 hover:bg-emerald-600 px-3 py-1 rounded-lg text-white text-xs"
            >
              New Episode
            </button>
          </div>
        )}

        {/* Gemini agent active banner */}
        {geminiMode && !done && (
          <div className="bg-violet-900/40 border border-violet-700 rounded-xl px-5 py-2.5 text-violet-300 text-sm flex items-center gap-2">
            <span className="animate-pulse">✦</span>
            <span>Gemini AI is controlling the grid — model: <strong>gemini-3-flash-preview</strong> · thinking: HIGH</span>
            {lastActionSource === 'gemini' && lastAction !== null && (
              <span className="ml-auto text-xs bg-violet-800 px-2 py-0.5 rounded-full">
                Last action: {lastAction}
              </span>
            )}
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard title="Total Demand"  value={obs?.demand?.toFixed(1) ?? '—'}          unit="MW" color="text-red-400"    icon="📊" />
          <StatCard title="Solar"         value={obs?.solar_generation?.toFixed(1) ?? '—'} unit="MW" color="text-yellow-400" icon="☀️" />
          <StatCard title="Wind"          value={obs?.wind_generation?.toFixed(1) ?? '—'}  unit="MW" color="text-blue-400"   icon="💨" />
          <StatCard title="Total Reward"  value={totalReward.toFixed(1)}                              color="text-violet-400" icon="🏆" />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <EnergyChart history={history} />
          </div>
          <div className="space-y-4">
            <BatteryGauge level={obs?.battery_storage ?? 0} />
            <StatCard
              title="Transmission Load"
              value={obs?.transmission_load?.toFixed(1) ?? '—'}
              unit="%"
              color={obs?.transmission_load > 90 ? 'text-red-400' : 'text-emerald-400'}
              icon="🔌"
            />
            <StatCard
              title="Time of Day"
              value={obs ? `${String(obs.time_of_day).padStart(2, '0')}:00` : '—'}
              color="text-slate-300"
              icon="🕐"
            />
          </div>
        </div>

        {/* Bottom row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <RegionPanel regionDemands={obs?.region_demands} blackout={info?.blackout} />
          <ActionPanel onAction={handleAction} disabled={done || loading} lastAction={lastAction} />
          <ScenarioSimulator activeTask={task} onSelect={handleTaskSelect} />
          <CarbonTracker history={history} />
        </div>
      </main>
    </div>
  );
}
