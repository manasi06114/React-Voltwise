export default function BatteryGauge({ state }) {
  const batteryLevel = state.battery_storage || 0
  const maxBattery = state.battery_capacity || 100

  return (
    <div className="card">
      <h3 style={{ marginBottom: '15px' }}>🔋 Battery Storage</h3>
      <div className="progress-bar" style={{ height: '20px' }}>
        <div 
          className="progress-fill" 
          style={{ width: `${(batteryLevel / maxBattery) * 100}%` }}
        />
      </div>
      <div style={{ marginTop: '10px', fontSize: '1.2em', fontWeight: 'bold' }}>
        {(batteryLevel || 0).toFixed(1)} / {(maxBattery || 100).toFixed(1)} MWh
      </div>
      <div style={{ marginTop: '5px', fontSize: '0.9em', opacity: 0.7 }}>
        {((batteryLevel / maxBattery) * 100).toFixed(1)}% Full
      </div>
    </div>
  )
}
