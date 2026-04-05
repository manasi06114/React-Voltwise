export default function StatCard({ title, value, color }) {
  return (
    <div className="card stat-card">
      <div className="stat-label">{title}</div>
      <div className="stat-value" style={{ color: color || '#00d4ff' }}>
        {value}
      </div>
    </div>
  )
}
