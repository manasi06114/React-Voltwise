const ACTIONS = [
  { id: 0, label: 'Redirect', icon: '↔️' },
  { id: 1, label: 'Charge', icon: '🔋' },
  { id: 2, label: 'Discharge', icon: '⚡' },
  { id: 3, label: 'Generator', icon: '🔧' },
  { id: 4, label: 'Curtail', icon: '🌿' },
  { id: 5, label: 'Redistribute', icon: '🔄' },
];

export default function ActionPanel({ onAction, disabled = false, lastAction }) {
  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Grid Actions</h3>
      <p className="section-subtitle">Manual dispatch and balancing commands</p>
      <div className="grid grid-cols-3 gap-2 mt-3">
        {ACTIONS.map(a => (
          <button
            key={a.id}
            onClick={() => onAction(a.id)}
            disabled={disabled}
            className={`action-pill ${lastAction === a.id ? 'action-pill-active' : ''}`}
          >
            <span>{a.icon}</span>
            <span>{a.label}</span>
          </button>
        ))}
      </div>
      {lastAction !== null && lastAction !== undefined && (
        <div className="mt-3 text-xs text-slate-500">
          Last action: <span className="font-semibold text-slate-700">{ACTIONS[lastAction]?.label}</span>
        </div>
      )}
    </div>
  );
}
