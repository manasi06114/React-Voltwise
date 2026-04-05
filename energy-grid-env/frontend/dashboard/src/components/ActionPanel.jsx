const ACTIONS = [
  { id: 0, label: 'Redirect Power',      icon: '↔️',  color: 'bg-blue-600 hover:bg-blue-500' },
  { id: 1, label: 'Charge Battery',      icon: '🔋',  color: 'bg-emerald-600 hover:bg-emerald-500' },
  { id: 2, label: 'Discharge Battery',   icon: '⚡',  color: 'bg-yellow-600 hover:bg-yellow-500' },
  { id: 3, label: 'Activate Generator',  icon: '🔧',  color: 'bg-orange-600 hover:bg-orange-500' },
  { id: 4, label: 'Curtail Renewable',   icon: '🌿',  color: 'bg-teal-600 hover:bg-teal-500' },
  { id: 5, label: 'Redistribute Power',  icon: '🔄',  color: 'bg-purple-600 hover:bg-purple-500' },
];

export default function ActionPanel({ onAction, disabled = false, lastAction }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-3">Manual Actions</h3>
      <div className="grid grid-cols-2 gap-2">
        {ACTIONS.map(a => (
          <button
            key={a.id}
            onClick={() => onAction(a.id)}
            disabled={disabled}
            className={`
              ${a.color} text-white text-sm font-medium px-3 py-2 rounded-lg
              flex items-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed
              ${lastAction === a.id ? 'ring-2 ring-white/30' : ''}
            `}
          >
            <span>{a.icon}</span>
            {a.label}
          </button>
        ))}
      </div>
      {lastAction !== null && lastAction !== undefined && (
        <p className="text-xs text-slate-500 mt-2">
          Last action: <span className="text-slate-400">{ACTIONS[lastAction]?.label}</span>
        </p>
      )}
    </div>
  );
}
