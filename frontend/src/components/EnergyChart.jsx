import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p>Step {label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="tip-row">
          <span className="tip-dot" style={{ background: entry.color }} />
          <span>{entry.name}</span>
          <strong>{Number(entry.value).toFixed(1)} MW</strong>
        </div>
      ))}
    </div>
  );
};

export default function EnergyChart({ history }) {
  const data = history.slice(-12).map((point) => ({
    step: `S${point.step}`,
    demand: Number(point.demand.toFixed(1)),
    renewable: Number((point.solar + point.wind).toFixed(1)),
  }));

  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="section-title">Total Supply</h3>
          <p className="section-subtitle">Demand bars and renewable trend</p>
        </div>
        <div className="mini-filter">Last 30 steps</div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(15, 23, 42, 0.08)" vertical={false} />
          <XAxis dataKey="step" stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <YAxis stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(109, 93, 252, 0.06)' }} />
          <Bar dataKey="demand" name="Demand" radius={[10, 10, 0, 0]} fill="#6d5dfc" maxBarSize={34} />
          <Line
            dataKey="renewable"
            name="Renewable"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={{ r: 3, strokeWidth: 2, fill: '#fff' }}
            activeDot={{ r: 5 }}
            type="monotone"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
