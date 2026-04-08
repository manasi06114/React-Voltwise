const SCENARIOS = [
  {
    id: 'easy',
    label: 'Single City',
    desc: 'Basic load balancing',
    badge: 'Easy',
    badgeColor: 'scenario-badge scenario-easy',
  },
  {
    id: 'medium',
    label: 'Multi Region',
    desc: 'Cross-region optimization',
    badge: 'Medium',
    badgeColor: 'scenario-badge scenario-medium',
  },
  {
    id: 'hard',
    label: 'Fluctuation',
    desc: 'Weather & demand surges',
    badge: 'Hard',
    badgeColor: 'scenario-badge scenario-hard',
  },
];

export default function ScenarioSimulator({ activeTask, onSelect }) {
  return (
    <div className="widget-panel panel-animate">
      <h3 className="section-title">Scenarios</h3>
      <p className="section-subtitle">Switch task complexity instantly</p>
      <div className="space-y-2 mt-3">
        {SCENARIOS.map(s => {
          const active = activeTask === s.id;
          return (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`scenario-row ${active ? 'scenario-row-active' : ''}`}
            >
              <div className="text-left">
                <span className="text-sm font-medium text-slate-700">{s.label}</span>
                <p className="text-[10px] text-slate-500 mt-0.5">{s.desc}</p>
              </div>
              <span className={s.badgeColor}>{s.badge}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
