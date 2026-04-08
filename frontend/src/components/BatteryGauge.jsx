export default function BatteryGauge({ level = 0 }) {
  const pct = Math.max(0, Math.min(100, level));

  const label = pct > 60 ? 'Healthy' : pct > 30 ? 'Moderate' : 'Critical';
  const color = pct > 60 ? '#10b981' : pct > 30 ? '#f59e0b' : '#ef4444';

  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Battery Storage</h3>
      <p className="section-subtitle">Charge and reserve health</p>

      <div className="battery-line">
        <div className="battery-track">
          <div className="battery-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
        <div className="battery-meta">
          <strong>{pct.toFixed(0)}%</strong>
          <span style={{ color }}>{label}</span>
        </div>
      </div>

      <p className="battery-note">
        {pct > 60
          ? 'Sufficient reserves for peak balancing.'
          : pct > 30
          ? 'Moderate reserve. Prioritize charging from renewable surplus.'
          : 'Low reserve detected. Reduce discharge actions and stabilize load.'}
      </p>
    </div>
  );
}
