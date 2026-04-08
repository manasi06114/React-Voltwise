const ACTION_NAMES = [
  'Redirect Power',
  'Charge Battery',
  'Discharge Battery',
  'Activate Generator',
  'Curtail Renewable',
  'Redistribute Power',
];

const ACTION_ICONS = ['arrow-right-left', 'battery-charging', 'zap', 'cog', 'leaf', 'refresh-cw'];
const ACTION_EMOJI = ['\u2194\uFE0F', '\u{1F50B}', '\u26A1', '\u2699\uFE0F', '\u{1F33F}', '\u{1F504}'];

export default function AIDecisionLog({ decisions = [], isActive }) {
  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between">
        <h3 className="section-title">AI Decision Log</h3>
        {isActive && (
          <span className="ai-active-badge">AI ACTIVE</span>
        )}
      </div>
      <p className="section-subtitle">Recent agent actions and reasoning</p>

      {decisions.length === 0 ? (
        <p className="text-xs text-slate-400 mt-4 text-center">
          {isActive ? 'Waiting for first AI decision...' : 'Enable AI mode to see decisions'}
        </p>
      ) : (
        <div className="ai-log-list mt-3">
          {decisions.slice(-8).reverse().map((d, i) => (
            <div key={i} className={`ai-log-entry ${i === 0 ? 'ai-log-latest' : ''}`}>
              <div className="ai-log-step">S{d.step}</div>
              <div className="ai-log-action">
                <span>{ACTION_EMOJI[d.action] || '?'}</span>
                <span className="font-semibold">{ACTION_NAMES[d.action] || `Action ${d.action}`}</span>
              </div>
              <div className={`ai-log-reward ${d.reward >= 0 ? 'positive' : 'negative'}`}>
                {d.reward >= 0 ? '+' : ''}{d.reward.toFixed(1)}
              </div>
              <div className="ai-log-source">
                {d.source === 'gemini' ? 'Gemini' : 'Mock'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
