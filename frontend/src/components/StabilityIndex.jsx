import { useState, useEffect } from 'react';
import { getStability } from '../api/gridApi';

export default function StabilityIndex({ task, refreshTrigger }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getStability(task).then(setData).catch(() => {});
  }, [task, refreshTrigger]);

  if (!data) return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Grid Stability</h3>
      <p className="section-subtitle">Waiting for data...</p>
    </div>
  );

  const { stability_index, components, label } = data;
  const color = label === 'stable' ? '#10b981' : label === 'warning' ? '#f59e0b' : '#ef4444';

  // SVG arc gauge
  const radius = 54;
  const circumference = Math.PI * radius; // half circle
  const offset = circumference - (stability_index / 100) * circumference;

  const bars = [
    { label: 'Transmission', value: components.transmission, color: '#6d5dfc' },
    { label: 'Supply/Demand', value: components.supply_demand, color: '#3b82f6' },
    { label: 'Battery', value: components.battery, color: '#10b981' },
    { label: 'Blackout Free', value: components.blackout_free, color: '#f59e0b' },
  ];

  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Grid Stability</h3>
      <p className="section-subtitle">Composite stability score</p>

      <div style={{ display: 'flex', justifyContent: 'center', margin: '16px 0 8px' }}>
        <svg width="130" height="80" viewBox="0 0 130 80">
          <path
            d="M 11 75 A 54 54 0 0 1 119 75"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path
            d="M 11 75 A 54 54 0 0 1 119 75"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.7s ease' }}
          />
          <text x="65" y="65" textAnchor="middle" style={{ fontSize: '28px', fontWeight: 700, fill: color }}>
            {Math.round(stability_index)}
          </text>
          <text x="65" y="78" textAnchor="middle" style={{ fontSize: '10px', fill: '#94a3b8' }}>
            / 100
          </text>
        </svg>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
        <span className={`status-chip ${label === 'stable' ? 'status-ok' : label === 'warning' ? 'status-warn' : 'status-danger'}`}>
          {label.charAt(0).toUpperCase() + label.slice(1)}
        </span>
      </div>

      <div className="space-y-2">
        {bars.map(b => (
          <div key={b.label}>
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>{b.label}</span>
              <span className="font-semibold tabular-nums">{b.value.toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${Math.min(100, b.value)}%`, background: b.color, transition: 'width 0.5s ease' }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
