export default function StatCard({ title, value, unit, color = 'text-emerald-400', icon }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        {icon && <span>{icon}</span>}
        {title}
      </div>
      <div className={`text-2xl font-bold ${color}`}>
        {value}
        {unit && <span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>}
      </div>
    </div>
  );
}
