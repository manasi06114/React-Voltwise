import { useState, useEffect, useRef } from 'react';
import { getRecoveryStatus } from '../api/gridApi';

const FAILURES = [
  { id: 'plant_shutdown', label: 'Plant Shutdown', icon: '\u{1F3ED}', desc: 'Generators offline' },
  { id: 'transmission_failure', label: 'Line Failure', icon: '\u{1F50C}', desc: 'Grid capacity -50%' },
  { id: 'demand_surge', label: 'Demand Spike', icon: '\u26A1', desc: 'Extreme +60% load' },
  { id: 'renewable_collapse', label: 'Renewable Collapse', icon: '\u{1F327}', desc: 'Solar & wind -70%' },
];

export default function EmergencyRecovery({ task, onInject, onClear }) {
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [recovery, setRecovery] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => {
    if (emergencyMode && recovery?.active_emergency) {
      pollRef.current = setInterval(() => {
        getRecoveryStatus(task).then(setRecovery).catch(() => {});
      }, 3000);
    }
    return () => clearInterval(pollRef.current);
  }, [emergencyMode, task, recovery?.active_emergency]);

  const handleInjectFailure = async (failureId) => {
    const intensity = failureId === 'demand_surge' ? 2.0 : 1.0;
    await onInject(failureId, intensity);
    const status = await getRecoveryStatus(task);
    setRecovery(status);
  };

  const handleEndEmergency = async () => {
    await onClear();
    setRecovery(null);
    setEmergencyMode(false);
  };

  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between">
        <h3 className="section-title">Emergency Recovery</h3>
        <div
          className="emergency-toggle"
          onClick={() => setEmergencyMode(v => !v)}
        >
          <span className="text-xs text-slate-500">{emergencyMode ? 'Active' : 'Off'}</span>
          <div className={`emergency-toggle-track ${emergencyMode ? 'active' : ''}`}>
            <div className="emergency-toggle-thumb" />
          </div>
        </div>
      </div>
      <p className="section-subtitle">Simulate grid failures & AI recovery</p>

      {!emergencyMode ? (
        <p className="text-xs text-slate-400 mt-4 text-center">
          Enable emergency mode to inject grid failures and test AI recovery capabilities.
        </p>
      ) : (
        <div className="mt-3">
          {!recovery?.active_emergency ? (
            <div className="grid grid-cols-2 gap-1.5">
              {FAILURES.map(f => (
                <button
                  key={f.id}
                  onClick={() => handleInjectFailure(f.id)}
                  className="scenario-inject-btn"
                  style={{ borderColor: 'rgba(239,68,68,0.3)' }}
                >
                  <span>{f.icon}</span>
                  <div className="text-left">
                    <span className="text-[10px] font-semibold">{f.label}</span>
                    <p className="text-[8px] text-slate-400">{f.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-slate-500">Recovery Progress</span>
                <span className="font-semibold tabular-nums" style={{ color: recovery.stability_restored ? '#10b981' : '#ef4444' }}>
                  {recovery.recovery_pct.toFixed(0)}%
                </span>
              </div>
              <div className="recovery-bar-track">
                <div
                  className="recovery-bar-fill"
                  style={{
                    width: `${recovery.recovery_pct}%`,
                    background: recovery.stability_restored ? '#10b981' : '#f59e0b',
                  }}
                />
              </div>

              <div className="flex justify-between items-center mt-3 text-xs">
                <span className="text-slate-400">
                  Steps: {recovery.steps_since_injection}
                </span>
                {recovery.stability_restored ? (
                  <span className="status-chip status-ok">Stabilized</span>
                ) : (
                  <span className="status-chip status-danger">Recovering</span>
                )}
              </div>

              <p className="text-[10px] text-slate-400 mt-2">
                Failure: {recovery.scenario?.replace(/_/g, ' ')}
              </p>

              <button
                onClick={handleEndEmergency}
                className="w-full mt-3 text-xs font-semibold py-2 rounded-lg border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 transition-colors cursor-pointer"
              >
                End Emergency
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
