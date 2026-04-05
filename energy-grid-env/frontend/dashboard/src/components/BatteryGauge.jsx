export default function BatteryGauge({ level = 0 }) {
  const pct = Math.max(0, Math.min(100, level));
  const color =
    pct > 60 ? 'bg-emerald-500' :
    pct > 30 ? 'bg-yellow-500' :
               'bg-red-500';

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-3">Battery Storage</h3>
      <div className="flex items-center gap-3">
        <div className="flex-1 h-5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${color}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-lg font-bold text-slate-200 w-14 text-right">{pct.toFixed(1)}%</span>
      </div>
      <div className="mt-2 text-xs text-slate-500">
        {pct > 60 ? 'Sufficient charge' : pct > 30 ? 'Moderate — consider charging' : 'Low — discharge limited'}
      </div>
    </div>
  );
}
