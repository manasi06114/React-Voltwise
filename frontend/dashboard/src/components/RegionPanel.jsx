export default function RegionPanel({ state }) {
  const regions = state.regions || []

  return (
    <div className="card section">
      <h2 className="section-title">📍 Regional Status</h2>
      <div className="region-grid">
        {regions.length > 0 ? (
          regions.slice(0, 4).map((region, index) => (
            <div key={index} className="region-item">
              <div className="region-name">{region.name || `Region ${index + 1}`}</div>
              <div className="region-stat">
                <span>Demand:</span>
                <strong>{(region.demand || 0).toFixed(1)} MW</strong>
              </div>
              <div className="region-stat">
                <span>Supply:</span>
                <strong>{(region.supply || 0).toFixed(1)} MW</strong>
              </div>
              <div className="region-stat">
                <span>Status:</span>
                <strong style={{ color: region.status === 'stable' ? '#51cf66' : '#ff6b6b' }}>
                  {region.status || 'unknown'}
                </strong>
              </div>
            </div>
          ))
        ) : (
          <div style={{ gridColumn: '1/-1', opacity: 0.5 }}>No region data available</div>
        )}
      </div>
    </div>
  )
}
