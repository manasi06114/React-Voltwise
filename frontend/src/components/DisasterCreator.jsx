import { useState } from 'react';

const DISASTERS = [
  { id: 'flood',             label: 'Flood',             icon: '\u{1F30A}', desc: 'Solar -90%, grid -60%, demand +20%', color: '#3b82f6' },
  { id: 'heavy_rain',        label: 'Heavy Rain',        icon: '\u{1F327}', desc: 'Solar -70%, wind +40%', color: '#6366f1' },
  { id: 'heatwave',          label: 'Heatwave',          icon: '\u{1F525}', desc: 'Demand +50%, solar +10%', color: '#f97316' },
  { id: 'cyclone',           label: 'Cyclone',           icon: '\u{1F300}', desc: 'All gen shutdown, grid -80%', color: '#8b5cf6' },
  { id: 'equipment_failure', label: 'Equipment Fail',    icon: '\u{1F527}', desc: 'Generators go offline', color: '#ef4444' },
  { id: 'grid_overload',     label: 'Grid Overload',     icon: '\u26A1',    desc: 'Demand +80%, grid stressed', color: '#dc2626' },
  { id: 'solar_eclipse',     label: 'Solar Eclipse',     icon: '\u{1F311}', desc: 'Solar output drops 95%', color: '#1e293b' },
  { id: 'night_peak',        label: 'Night Peak',        icon: '\u{1F303}', desc: 'No solar, demand peaks', color: '#334155' },
];

export default function DisasterCreator({ onInject, onClear, activeScenario }) {
  const [severity, setSeverity] = useState(1.0);
  const [injecting, setInjecting] = useState(false);

  const handleInject = async (disasterId) => {
    setInjecting(true);
    try {
      await onInject(disasterId, severity);
    } finally {
      setInjecting(false);
    }
  };

  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Disaster Simulator</h3>
      <p className="section-subtitle">Create real-world crisis scenarios for Pune grid</p>

      <div className="flex items-center gap-2 mt-3 mb-2">
        <span className="text-xs text-slate-400">Severity</span>
        <input
          type="range"
          min="0.5" max="2.0" step="0.1"
          value={severity}
          onChange={e => setSeverity(parseFloat(e.target.value))}
          style={{ flex: 1, accentColor: '#ef4444' }}
        />
        <span className="text-xs font-bold tabular-nums" style={{
          minWidth: 32,
          color: severity > 1.5 ? '#ef4444' : severity > 1.0 ? '#f59e0b' : '#10b981',
        }}>
          {severity.toFixed(1)}x
        </span>
      </div>

      <div className="grid grid-cols-2 gap-1.5 mt-2">
        {DISASTERS.map(d => (
          <button
            key={d.id}
            onClick={() => handleInject(d.id)}
            disabled={injecting}
            className={`disaster-btn ${activeScenario === d.id ? 'disaster-btn-active' : ''}`}
            style={{ '--disaster-color': d.color }}
          >
            <span style={{ fontSize: 18 }}>{d.icon}</span>
            <div className="text-left" style={{ flex: 1 }}>
              <span className="text-[11px] font-semibold">{d.label}</span>
              <p className="text-[8px] text-slate-400 mt-0.5">{d.desc}</p>
            </div>
          </button>
        ))}
      </div>

      {activeScenario && (
        <button
          onClick={onClear}
          disabled={injecting}
          className="w-full mt-2 text-xs font-semibold py-2 rounded-lg border border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors cursor-pointer"
        >
          Restore Normal Conditions
        </button>
      )}
    </div>
  );
}
