import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p>Step {label}</p>
      {payload.map((p, i) => (
        <div key={i} className="tip-row">
          <span className="tip-dot" style={{ background: p.fill || p.color }} />
          <span>{p.name}</span>
          <strong>{p.value} t</strong>
        </div>
      ))}
    </div>
  );
};

export default function CarbonTracker({ history }) {
  const data = history.slice(-12).map((h) => ({
    step: `S${h.step}`,
    co2_saved: parseFloat(((h.solar + h.wind) * 0.4).toFixed(1)),
    fossil: parseFloat((h.fossil_fuel * 0.8).toFixed(1)),
  }));

  const totalSaved = history.reduce((s, h) => s + (h.solar + h.wind) * 0.4, 0);
  const totalFossil = history.reduce((s, h) => s + h.fossil_fuel * 0.8, 0);

  // Per-source breakdown from full history
  const totalSolar = history.reduce((s, h) => s + h.solar * 0.4, 0);
  const totalWind = history.reduce((s, h) => s + h.wind * 0.4, 0);
  const totalRenewable = totalSolar + totalWind;

  const sources = [
    { label: 'Solar', value: totalSolar, pct: totalRenewable > 0 ? (totalSolar / totalRenewable) * 100 : 0, color: '#f59e0b' },
    { label: 'Wind', value: totalWind, pct: totalRenewable > 0 ? (totalWind / totalRenewable) * 100 : 0, color: '#3b82f6' },
  ];

  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between mb-1">
        <h3 className="section-title">Carbon Tracker</h3>
        <span className="text-emerald-600 text-xs font-semibold tabular-nums">
          {totalSaved.toFixed(1)}t saved
        </span>
      </div>
      <p className="section-subtitle mb-3">Carbon savings trend and fossil dependency</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(15, 23, 42, 0.08)" vertical={false} />
          <XAxis dataKey="step" stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <YAxis stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Line type="monotone" dataKey="co2_saved" name="CO2 Saved" stroke="#6d5dfc" strokeWidth={2.5} dot={{ r: 3, fill: '#fff' }} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="fossil" name="Fossil CO2" stroke="#ef4444" strokeWidth={2} dot={false} strokeDasharray="6 4" />
        </LineChart>
      </ResponsiveContainer>

      {/* Per-source breakdown */}
      <div style={{ borderTop: '1px solid var(--line)', marginTop: 10, paddingTop: 8 }}>
        <p className="text-[10px] text-slate-400 font-semibold mb-2">Savings by Source</p>
        {sources.map(s => (
          <div key={s.label} className="mb-1.5">
            <div className="flex justify-between text-[10px] text-slate-500 mb-0.5">
              <span className="flex items-center gap-1">
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.color, display: 'inline-block' }} />
                {s.label}
              </span>
              <span className="font-semibold tabular-nums">{s.value.toFixed(1)}t ({s.pct.toFixed(0)}%)</span>
            </div>
            <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${s.pct}%`, background: s.color, transition: 'width 0.5s ease' }} />
            </div>
          </div>
        ))}
        <div className="flex justify-between text-[10px] text-slate-400 mt-2">
          <span>Fossil emitted: {totalFossil.toFixed(1)}t</span>
          <span className="font-semibold text-emerald-600">Net saved: {(totalSaved - totalFossil).toFixed(1)}t</span>
        </div>
      </div>
    </div>
  );
}
