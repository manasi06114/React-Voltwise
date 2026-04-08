import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import { getForecast } from '../api/gridApi';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p>{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="tip-row">
          <span className="tip-dot" style={{ background: p.color }} />
          <span>{p.name}</span>
          <strong>{Number(p.value).toFixed(1)} MW</strong>
        </div>
      ))}
    </div>
  );
};

export default function RenewableForecast({ task, refreshTrigger }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getForecast(task).then(setData).catch(() => {});
  }, [task, refreshTrigger]);

  if (!data) return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Renewable Forecast</h3>
      <p className="section-subtitle">Loading forecast...</p>
    </div>
  );

  const chartData = data.forecast.map(f => ({
    hour: `${String(f.hour).padStart(2, '0')}:00`,
    Solar: f.solar_mw,
    Wind: f.wind_mw,
  }));

  const peakSolar = data.forecast.reduce((max, f) => f.solar_mw > max.solar_mw ? f : max, data.forecast[0]);
  const peakWind = data.forecast.reduce((max, f) => f.wind_mw > max.wind_mw ? f : max, data.forecast[0]);
  const totalDaily = data.forecast.reduce((s, f) => s + f.solar_mw + f.wind_mw, 0);

  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between mb-1">
        <h3 className="section-title">Renewable Forecast</h3>
        <span className="text-xs text-slate-500 tabular-nums">24h ahead</span>
      </div>
      <p className="section-subtitle mb-3">Predicted solar and wind generation</p>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(15,23,42,0.08)" vertical={false} />
          <XAxis dataKey="hour" stroke="#94a3b8" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} interval={3} />
          <YAxis stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            x={`${String(data.current_hour).padStart(2, '0')}:00`}
            stroke="#6d5dfc"
            strokeDasharray="4 4"
            label={{ value: 'Now', position: 'top', fontSize: 10, fill: '#6d5dfc' }}
          />
          <Area type="monotone" dataKey="Solar" stackId="1" stroke="#f59e0b" fill="rgba(245,158,11,0.25)" strokeWidth={2} />
          <Area type="monotone" dataKey="Wind" stackId="1" stroke="#3b82f6" fill="rgba(59,130,246,0.2)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
        <div>
          <p className="text-slate-400">Peak Solar</p>
          <p className="font-semibold text-amber-600">{peakSolar.solar_mw} MW @ {String(peakSolar.hour).padStart(2, '0')}h</p>
        </div>
        <div>
          <p className="text-slate-400">Peak Wind</p>
          <p className="font-semibold text-blue-600">{peakWind.wind_mw} MW @ {String(peakWind.hour).padStart(2, '0')}h</p>
        </div>
        <div>
          <p className="text-slate-400">Total 24h</p>
          <p className="font-semibold text-violet-600">{totalDaily.toFixed(0)} MWh</p>
        </div>
      </div>
    </div>
  );
}
