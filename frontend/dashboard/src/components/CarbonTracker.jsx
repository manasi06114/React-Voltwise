export default function CarbonTracker({ state }) {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '15px' }}>🌍 Carbon Impact</h3>
      <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: '#51cf66', marginBottom: '10px' }}>
        {(state.carbon_saved || 0).toFixed(1)} kg CO₂ Saved
      </div>
      <div style={{ fontSize: '0.9em', opacity: 0.7 }}>
        <div>Fossil Fuel Used: {(state.fossil_generation || 0).toFixed(1)} MW</div>
        <div>Renewable Used: {((state.solar_generation || 0) + (state.wind_generation || 0)).toFixed(1)} MW</div>
      </div>
    </div>
  )
}
