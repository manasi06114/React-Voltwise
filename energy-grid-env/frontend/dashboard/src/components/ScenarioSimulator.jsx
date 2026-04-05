const SCENARIOS = [
  { id: 'easy',   label: 'Single City Grid',       badge: 'Easy',   color: 'bg-emerald-900 text-emerald-300 border-emerald-700' },
  { id: 'medium', label: 'Multi-Region Grid',       badge: 'Medium', color: 'bg-yellow-900 text-yellow-300 border-yellow-700' },
  { id: 'hard',   label: 'Renewable Fluctuation',  badge: 'Hard',   color: 'bg-red-900 text-red-300 border-red-700' },
];

export default function ScenarioSimulator({ activeTask, onSelect }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-3">Scenario Simulator</h3>
      <div className="space-y-2">
        {SCENARIOS.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`
              w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-all
              ${activeTask === s.id
                ? 'bg-slate-600 border-slate-400'
                : 'bg-slate-700 border-slate-600 hover:bg-slate-600'}
            `}
          >
            <span className="text-slate-200 text-sm font-medium">{s.label}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${s.color}`}>{s.badge}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
