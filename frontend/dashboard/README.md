# VoltWise Dashboard

A modern React dashboard for the VoltWise Energy Grid Simulator.

## Getting Started

### Development

```bash
npm install
npm run dev
```

The dashboard will start at `http://localhost:5173`

### Build

```bash
npm run build
npm run preview
```

## Features

- **Real-time Grid Monitoring** - Live energy distribution, demand, and supply metrics
- **Energy Distribution Chart** - Visualize solar, wind, and fossil fuel generation
- **Regional Status** - Monitor grid conditions across different regions
- **Battery Management** - Track energy storage levels
- **Carbon Tracking** - Monitor environmental impact
- **Grid Actions** - Send commands to control grid operations
- **Scenario Simulator** - Test AI responses to different grid conditions
- **AI Integration** - Powered by Gemini AI for intelligent decision-making

## API Integration

The dashboard connects to the FastAPI backend at `http://localhost:8000`

Key endpoints:

- `POST /env/create-session` - Create a new environment session
- `POST /env/{session_id}/reset` - Reset the grid
- `POST /env/{session_id}/step` - Execute an action
- `POST /env/{session_id}/gemini-step` - AI-powered step
- `POST /env/{session_id}/simulate-scenario` - Simulate scenarios
