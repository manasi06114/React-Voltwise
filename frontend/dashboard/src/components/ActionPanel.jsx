import { useState } from 'react'

export default function ActionPanel({ onAction }) {
  const [selectedAction, setSelectedAction] = useState(0)

  const actions = [
    { id: 0, name: 'Redirect Power', icon: '↔️' },
    { id: 1, name: 'Charge Battery', icon: '⬆️' },
    { id: 2, name: 'Discharge Battery', icon: '⬇️' },
    { id: 3, name: 'Activate Generator', icon: '⚙️' },
    { id: 4, name: 'Curtail Renewable', icon: '❌' },
    { id: 5, name: 'Balance Load', icon: '⚖️' },
  ]

  return (
    <div className="card section">
      <h2 className="section-title">🎮 Grid Actions</h2>
      <p style={{ marginBottom: '15px', opacity: 0.8 }}>Select an action to control the grid:</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', marginBottom: '15px' }}>
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={() => setSelectedAction(action.id)}
            style={{
              background: selectedAction === action.id 
                ? 'linear-gradient(45deg, #00d4ff, #7b2ff7)' 
                : 'rgba(255, 255, 255, 0.1)',
              border: selectedAction === action.id 
                ? '2px solid #00d4ff' 
                : '1px solid rgba(255, 255, 255, 0.2)',
              padding: '12px 8px',
              textAlign: 'center',
              cursor: 'pointer',
              borderRadius: '8px',
              transition: 'all 0.3s ease'
            }}
          >
            <div style={{ fontSize: '1.5em', marginBottom: '5px' }}>{action.icon}</div>
            <div style={{ fontSize: '0.85em' }}>{action.name}</div>
          </button>
        ))}
      </div>

      <button 
        onClick={() => onAction(selectedAction)}
        style={{
          width: '100%',
          padding: '15px',
          fontSize: '1.1em',
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #00d4ff, #7b2ff7)',
          border: 'none',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Execute Action
      </button>
    </div>
  )
}
