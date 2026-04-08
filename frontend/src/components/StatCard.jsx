const TONE_MAP = {
  danger: { text: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)' },
  success: { text: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' },
  info: { text: '#3b82f6', bg: 'rgba(59, 130, 246, 0.09)' },
  accent: { text: '#6d5dfc', bg: 'rgba(109, 93, 252, 0.1)' },
};

export default function StatCard({ title, value, unit, tone = 'success', icon }) {
  const colors = TONE_MAP[tone] ?? TONE_MAP.success;

  return (
    <div className="widget-card panel-animate">
      <div className="widget-head">
        <span>{title}</span>
        {icon && (
          <span className="widget-icon" style={{ background: colors.bg, color: colors.text }}>
            {icon}
          </span>
        )}
      </div>
      <div className="widget-value" style={{ color: colors.text }}>
        {value}
        {unit && <small>{unit}</small>}
      </div>
      <p className="widget-note">Live grid metric</p>
    </div>
  );
}
