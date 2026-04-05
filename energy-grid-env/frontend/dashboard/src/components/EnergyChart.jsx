import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export default function EnergyChart({ history }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-4">Energy Overview (last 24 steps)</h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={history} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="step" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit=" MW" />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="demand"          stroke="#f87171" strokeWidth={2} dot={false} name="Demand" />
          <Line type="monotone" dataKey="solar"           stroke="#fbbf24" strokeWidth={2} dot={false} name="Solar" />
          <Line type="monotone" dataKey="wind"            stroke="#60a5fa" strokeWidth={2} dot={false} name="Wind" />
          <Line type="monotone" dataKey="fossil_fuel"     stroke="#f97316" strokeWidth={1} dot={false} name="Fossil" strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
