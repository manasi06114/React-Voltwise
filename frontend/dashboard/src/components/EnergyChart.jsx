export default function EnergyChart({ state }) {
  if (!state) return null

  const totalGeneration = state.solar_generation + state.wind_generation + state.fossil_generation
  const maxValue = Math.max(state.demand, totalGeneration, 200)

  return (
    <div className="chart-container">
      <h3 className="chart-title">Energy Distribution</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
        {/* Demand Bar */}
        <div>
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '0.9em', marginBottom: '5px' }}>
              Total Demand: <strong>{state.demand?.toFixed(1) || 0} MW</strong>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(state.demand / maxValue) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Supply Bar */}
        <div>
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '0.9em', marginBottom: '5px' }}>
              Total Supply: <strong>{totalGeneration?.toFixed(1) || 0} MW</strong>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(totalGeneration / maxValue) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Energy Sources */}
      <div style={{ marginTop: '30px' }}>
        <h4 style={{ marginBottom: '15px' }}>Energy Sources</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div style={{ background: 'rgba(255, 215, 61, 0.1)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255, 215, 61, 0.3)' }}>
            <div style={{ fontSize: '0.9em', opacity: 0.8 }}>☀️ Solar</div>
            <div style={{ fontSize: '1.3em', fontWeight: 'bold' }}>{state.solar_generation?.toFixed(1) || 0} MW</div>
          </div>
          
          <div style={{ background: 'rgba(100, 200, 255, 0.1)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(100, 200, 255, 0.3)' }}>
            <div style={{ fontSize: '0.9em', opacity: 0.8 }}>💨 Wind</div>
            <div style={{ fontSize: '1.3em', fontWeight: 'bold' }}>{state.wind_generation?.toFixed(1) || 0} MW</div>
          </div>

          <div style={{ background: 'rgba(160, 120, 80, 0.1)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(160, 120, 80, 0.3)' }}>
            <div style={{ fontSize: '0.9em', opacity: 0.8 }}>⛽ Fossil</div>
            <div style={{ fontSize: '1.3em', fontWeight: 'bold' }}>{state.fossil_generation?.toFixed(1) || 0} MW</div>
          </div>
        </div>
      </div>
    </div>
  )
}
