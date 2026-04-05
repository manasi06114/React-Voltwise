import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function CarbonTracker({ history }) {
  const data = history.slice(-12).map((h, i) => ({
    step: h.step,
    co2_saved: parseFloat((h.solar + h.wind) * 0.4).toFixed(1),
    fossil: parseFloat(h.fossil_fuel * 0.8).toFixed(1),
  }));

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-1">Carbon Emission Tracker</h3>
      <p className="text-xs text-slate-500 mb-3">Estimated CO₂ saved vs fossil usage (tonnes/step)</p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} margin={{ top: 0, right: 5, left: -20, bottom: 0 }}>
          <XAxis dataKey="step" stroke="#64748b" tick={{ fontSize: 10 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Bar dataKey="co2_saved" name="CO₂ Saved" radius={[3,3,0,0]}>
            {data.map((_, i) => <Cell key={i} fill="#34d399" />)}
          </Bar>
          <Bar dataKey="fossil" name="Fossil CO₂" radius={[3,3,0,0]}>
            {data.map((_, i) => <Cell key={i} fill="#f97316" />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
