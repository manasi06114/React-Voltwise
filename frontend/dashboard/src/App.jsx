import { useState, useEffect } from 'react'
import './App.css'
import StatCard from './components/StatCard'
import EnergyChart from './components/EnergyChart'
import RegionPanel from './components/RegionPanel'
import BatteryGauge from './components/BatteryGauge'
import CarbonTracker from './components/CarbonTracker'
import ScenarioSimulator from './components/ScenarioSimulator'
import ActionPanel from './components/ActionPanel'
import * as gridApi from './api/gridApi'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [state, setState] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [autoStep, setAutoStep] = useState(false)

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const session = await gridApi.createSession()
        setSessionId(session.session_id)
        
        const initialState = await gridApi.resetEnv(session.session_id)
        setState(initialState)
        setLoading(false)
      } catch (err) {
        setError('Failed to initialize environment: ' + err.message)
        setLoading(false)
      }
    }

    initSession()
  }, [])

  // Auto-step if enabled
  useEffect(() => {
    if (!autoStep || !sessionId) return

    const interval = setInterval(async () => {
      try {
        const result = await gridApi.geminiStep(sessionId)
        setState(result.state)
      } catch (err) {
        console.error('Auto-step error:', err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [autoStep, sessionId])

  const handleStep = async (action) => {
    if (!sessionId) return
    try {
      const result = await gridApi.step(sessionId, action)
      setState(result.state)
    } catch (err) {
      setError('Failed to execute action: ' + err.message)
    }
  }

  const handleGeminiStep = async () => {
    if (!sessionId) return
    try {
      const result = await gridApi.geminiStep(sessionId)
      setState(result.state)
    } catch (err) {
      setError('Failed to execute Gemini step: ' + err.message)
    }
  }

  const handleReset = async () => {
    if (!sessionId) return
    try {
      setLoading(true)
      const result = await gridApi.resetEnv(sessionId)
      setState(result)
      setLoading(false)
    } catch (err) {
      setError('Failed to reset environment: ' + err.message)
      setLoading(false)
    }
  }

  const handleScenario = async (scenarioName) => {
    if (!sessionId) return
    try {
      const result = await gridApi.simulateScenario(sessionId, scenarioName)
      setState(result.state)
    } catch (err) {
      setError('Failed to simulate scenario: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">Loading Energy Grid Dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">{error}</div>
        <button onClick={handleReset}>Retry</button>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="dashboard">
        <div className="loading">No state available</div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="header">
        <h1>⚡ VoltWise</h1>
        <p>AI-Powered Smart Grid Optimization</p>
      </div>

      {/* Error Alert */}
      {error && <div className="error">{error}</div>}

      {/* Control Panel */}
      <div className="card section">
        <h2 className="section-title">Control Panel</h2>
        <div className="button-group">
          <button onClick={handleReset}>🔄 Reset Grid</button>
          <button onClick={handleGeminiStep}>🤖 Gemini Step</button>
          <button onClick={() => setAutoStep(!autoStep)}>
            {autoStep ? '⏸️ Stop Auto' : '▶️ Auto Step'}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid-container">
        <StatCard 
          title="Demand" 
          value={state.demand ? `${state.demand.toFixed(1)} MW` : 'N/A'}
          color="#ff6b6b"
        />
        <StatCard 
          title="Supply" 
          value={state.total_generation ? `${state.total_generation.toFixed(1)} MW` : 'N/A'}
          color="#51cf66"
        />
        <StatCard 
          title="Renewable %" 
          value={state.renewable_percentage ? `${state.renewable_percentage.toFixed(1)}%` : 'N/A'}
          color="#00d4ff"
        />
        <StatCard 
          title="Grid Stability" 
          value={state.grid_stability !== undefined ? `${(state.grid_stability * 100).toFixed(1)}%` : 'N/A'}
          color="#ffd93d"
        />
      </div>

      {/* Energy Distribution Chart */}
      <EnergyChart state={state} />

      {/* Battery and Carbon Status */}
      <div className="grid-container">
        <BatteryGauge state={state} />
        <CarbonTracker state={state} />
      </div>

      {/* Regional Overview */}
      <RegionPanel state={state} />

      {/* Action Panel */}
      <ActionPanel onAction={handleStep} />

      {/* Scenario Simulator */}
      <ScenarioSimulator onScenario={handleScenario} />

      {/* Raw State Debug (optional) */}
      <details style={{ marginTop: '30px' }}>
        <summary style={{ cursor: 'pointer', padding: '10px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
          Debug: Raw State
        </summary>
        <pre style={{ marginTop: '10px', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', fontSize: '0.8em', overflow: 'auto' }}>
          {JSON.stringify(state, null, 2)}
        </pre>
      </details>
    </div>
  )
}

export default App
