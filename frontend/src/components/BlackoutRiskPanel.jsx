import { useState, useEffect } from 'react';
import { getBlackoutRisk } from '../api/gridApi';

function RiskCircle({ name, risk, level }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (risk / 100) * circumference;
  const color = level === 'green' ? '#10b981' : level === 'yellow' ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="5" />
        <circle
          cx="36" cy="36" r={radius} fill="none"
          stroke={color} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 36 36)"
          style={{ transition: 'stroke-dashoffset 0.7s ease' }}
        />
        <text x="36" y="34" textAnchor="middle" style={{ fontSize: '14px', fontWeight: 700, fill: color }}>
          {risk.toFixed(0)}%
        </text>
        <text x="36" y="46" textAnchor="middle" style={{ fontSize: '8px', fill: '#94a3b8' }}>
          risk
        </text>
      </svg>
      <p className="text-xs text-slate-600 font-medium mt-1">{name}</p>
    </div>
  );
}

export default function BlackoutRiskPanel({ task, refreshTrigger }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getBlackoutRisk(task).then(setData).catch(() => {});
  }, [task, refreshTrigger]);

  if (!data) return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Blackout Risk</h3>
      <p className="section-subtitle">Loading risk data...</p>
    </div>
  );

  const maxRisk = data.regions.reduce((m, r) => r.risk_pct > m.risk_pct ? r : m, data.regions[0]);
  const allSafe = data.regions.every(r => r.level === 'green');

  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Blackout Risk</h3>
      <p className="section-subtitle">Per-region blackout probability</p>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, margin: '16px 0' }}>
        {data.regions.map(r => (
          <RiskCircle key={r.name} name={r.name} risk={r.risk_pct} level={r.level} />
        ))}
      </div>

      <p className="text-xs text-center" style={{ color: allSafe ? '#10b981' : '#ef4444', fontWeight: 600 }}>
        {allSafe
          ? 'All regions within safe parameters'
          : `${maxRisk.name} at ${maxRisk.level === 'red' ? 'critical' : 'elevated'} risk (${maxRisk.risk_pct.toFixed(0)}%)`}
      </p>
    </div>
  );
}
