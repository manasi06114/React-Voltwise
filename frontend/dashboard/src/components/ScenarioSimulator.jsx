import { useState } from 'react'

export default function ScenarioSimulator({ onScenario }) {
  const [selectedScenario, setSelectedScenario] = useState('normal')

  const scenarios = [
    { id: 'normal', name: 'Normal Operation', icon: '😊' },
    { id: 'demand_spike', name: 'Demand Spike', icon: '📈' },
    { id: 'renewable_drop', name: 'Renewable Drop', icon: '⬇️' },
    { id: 'transmission_failure', name: 'Transmission Failure', icon: '⚡' },
    { id: 'storage_failure', name: 'Battery Failure', icon: '🔋' },
    { id: 'storm', name: 'Storm Conditions', icon: '⛈️' },
  ]

  return (
    <div className="card section">
      <h2 className="section-title">🎬 Scenario Simulator</h2>
      <p style={{ marginBottom: '15px', opacity: 0.8 }}>Test how the AI responds to different grid conditions:</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginBottom: '15px' }}>
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => setSelectedScenario(scenario.id)}
            style={{
              background: selectedScenario === scenario.id 
                ? 'linear-gradient(45deg, #ff6b6b, #ff8e8e)' 
                : 'rgba(255, 255, 255, 0.1)',
              border: selectedScenario === scenario.id 
                ? '2px solid #ff6b6b' 
                : '1px solid rgba(255, 255, 255, 0.2)',
              padding: '12px 8px',
              textAlign: 'center',
              cursor: 'pointer',
              borderRadius: '8px',
              transition: 'all 0.3s ease'
            }}
          >
            <div style={{ fontSize: '1.5em', marginBottom: '5px' }}>{scenario.icon}</div>
            <div style={{ fontSize: '0.8em' }}>{scenario.name}</div>
          </button>
        ))}
      </div>

      <button 
        onClick={() => onScenario(selectedScenario)}
        style={{
          width: '100%',
          padding: '15px',
          fontSize: '1.1em',
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #ff6b6b, #ff8e8e)',
          border: 'none',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Activate Scenario
      </button>
    </div>
  )
}
