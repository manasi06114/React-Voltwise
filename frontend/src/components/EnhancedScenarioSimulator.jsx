import { useState } from 'react';
import { injectScenario, clearScenario } from '../api/gridApi';

const TASKS = [
  { id: 'easy', label: 'Single City', badge: 'Easy', cls: 'scenario-easy' },
  { id: 'medium', label: 'Multi Region', badge: 'Medium', cls: 'scenario-medium' },
  { id: 'hard', label: 'Fluctuation', badge: 'Hard', cls: 'scenario-hard' },
];

const SCENARIOS = [
  { id: 'demand_surge', label: 'Demand Surge', icon: '\u{1F4C8}', desc: '+30% load' },
  { id: 'solar_install', label: 'Solar Install', icon: '\u2600', desc: '+50% solar' },
  { id: 'wind_failure', label: 'Wind Failure', icon: '\u{1F32C}', desc: '-70% wind' },
  { id: 'storm', label: 'Storm', icon: '\u26C8', desc: 'Weather event' },
  { id: 'transmission_failure', label: 'Line Failure', icon: '\u{1F50C}', desc: '-50% capacity' },
];

export default function EnhancedScenarioSimulator({ task, onSelect, onScenarioInject, onScenarioClear, activeScenario }) {
  const [intensity, setIntensity] = useState(1.0);
  const [injecting, setInjecting] = useState(false);

  const handleInject = async (scenarioId) => {
    setInjecting(true);
    try {
      await onScenarioInject(scenarioId, intensity);
    } finally {
      setInjecting(false);
    }
  };

  const handleClear = async () => {
    setInjecting(true);
    try {
      await onScenarioClear();
    } finally {
      setInjecting(false);
    }
  };

  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Scenarios</h3>
      <p className="section-subtitle">Task difficulty & scenario injection</p>

      {/* Task switcher */}
      <div className="space-y-1.5 mt-3">
        {TASKS.map(t => (
          <button
            key={t.id}
            onClick={() => onSelect(t.id)}
            className={`scenario-row ${task === t.id ? 'scenario-row-active' : ''}`}
          >
            <span className="text-sm font-medium text-slate-700">{t.label}</span>
            <span className={`scenario-badge ${t.cls}`}>{t.badge}</span>
          </button>
        ))}
      </div>

      {/* Scenario injection */}
      <div style={{ borderTop: '1px solid var(--line)', marginTop: 12, paddingTop: 10 }}>
        <p className="text-xs font-semibold text-slate-600 mb-2">Inject Scenario</p>

        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-slate-400">Intensity</span>
          <input
            type="range"
            min="0.5" max="2.0" step="0.1"
            value={intensity}
            onChange={e => setIntensity(parseFloat(e.target.value))}
            style={{ flex: 1, accentColor: '#6d5dfc' }}
          />
          <span className="text-xs font-semibold tabular-nums text-slate-600" style={{ minWidth: 30 }}>
            {intensity.toFixed(1)}x
          </span>
        </div>

        <div className="grid grid-cols-2 gap-1.5">
          {SCENARIOS.map(s => (
            <button
              key={s.id}
              onClick={() => handleInject(s.id)}
              disabled={injecting}
              className={`scenario-inject-btn ${activeScenario === s.id ? 'scenario-inject-active' : ''}`}
            >
              <span>{s.icon}</span>
              <div className="text-left">
                <span className="text-[10px] font-semibold">{s.label}</span>
                <p className="text-[8px] text-slate-400">{s.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {activeScenario && (
          <button
            onClick={handleClear}
            disabled={injecting}
            className="w-full mt-2 text-xs font-semibold py-2 rounded-lg border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 transition-colors cursor-pointer"
          >
            Clear Scenario
          </button>
        )}
      </div>
    </div>
  );
}
