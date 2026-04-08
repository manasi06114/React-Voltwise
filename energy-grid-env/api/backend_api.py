"""
FastAPI Backend
Exposes the energy-grid environment and simulation state over HTTP so the
React dashboard can poll live data and send actions.

Run:
    uvicorn api.backend_api:app --reload --port 8000

Supports multiple API keys with automatic rotation when quotas are exhausted.
"""

import sys
import os
import math
import copy
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from env import EnergyGridEnv
from reward_engine import RewardEngine
from grid_simulator import GridSimulator, Region
from agent.model import GeminiGridAgent, ApiKeyError
from agent.mock_model import MockGeminiGridAgent
from api.key_manager import get_key_manager

app = FastAPI(
    title="VoltWise — Energy Grid API",
    description="Smart Grid simulation backend powered by Gemini AI",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
_envs: Dict[str, EnergyGridEnv] = {}
_reward_engine = RewardEngine()
_gemini_agent: Optional[GeminiGridAgent] = None
_key_manager = None
_original_regions: Dict[str, list] = {}  # stored originals for scenario restore
_active_scenarios: Dict[str, dict] = {}  # track injected scenarios per task


def _init_key_manager():
    """Initialize the key manager."""
    global _key_manager
    if _key_manager is None:
        _key_manager = get_key_manager()
    return _key_manager


def _get_gemini_agent() -> GeminiGridAgent:
    """Get or create the Gemini agent with the current API key."""
    global _gemini_agent
    
    # Initialize key manager
    key_manager = _init_key_manager()
    
    # Get a fresh API key (could be rotated)
    api_key = key_manager.get_key()
    
    # Always create a fresh agent with the current key
    _gemini_agent = GeminiGridAgent(api_key=api_key)
    return _gemini_agent, key_manager


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task: str = "medium"


class StepRequest(BaseModel):
    task: str = "medium"
    action: int


class GeminiStepRequest(BaseModel):
    task: str = "medium"


class ScenarioInjectRequest(BaseModel):
    task: str = "medium"
    scenario: str
    intensity: float = 1.0


class ScenarioClearRequest(BaseModel):
    task: str = "medium"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "VoltWise Energy Grid API is running",
        "version": "2.0.0",
        "features": ["Multi-API-Key Support", "Automatic Key Rotation", "Gemini AI Integration"]
    }


@app.get("/api-keys/status")
def get_api_key_status():
    """Get the current API key manager status."""
    try:
        key_manager = _init_key_manager()
        status = key_manager.get_status()
        return {
            "total_keys": status['total_keys'],
            "available_keys": status['available_keys'],
            "failed_keys": status['failed_keys'],
            "current_key_index": status['current_key_index'],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"API Key Manager Error: {str(e)}")


@app.get("/health")
def health():
    try:
        key_manager = _init_key_manager()
        status = key_manager.get_status()
        return {
            "status": "ok",
            "gemini_agent": True,
            "api_key_manager": {
                "total_keys": status['total_keys'],
                "available_keys": status['available_keys'],
                "failed_keys": status['failed_keys'],
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "gemini_agent": False,
            "error": str(e),
        }


@app.post("/env/reset")
def reset_env(req: ResetRequest):
    """Reset (or create) a simulation environment for the given task."""
    if req.task not in ("easy", "medium", "hard"):
        raise HTTPException(status_code=400, detail=f"Unknown task: {req.task}")
    env = EnergyGridEnv(task=req.task)
    _envs[req.task] = env
    obs = env.reset()
    return {"task": req.task, "observation": obs, "step": 0, "session_id": req.task}


@app.post("/env/create-session")
def create_session():
    """Backward compatibility - creates a session and returns session_id."""
    task = "medium"
    env = EnergyGridEnv(task=task)
    _envs[task] = env
    obs = env.reset()
    return {"session_id": task, "task": task}


@app.post("/env/step")
def step_env(req: StepRequest):
    """Apply a manual action and advance the simulation by one time-step."""
    env = _envs.get(req.task)
    if env is None:
        raise HTTPException(status_code=404,
                            detail="Environment not found. Call /env/reset first.")
    if not (0 <= req.action <= 5):
        raise HTTPException(status_code=400, detail="action must be 0–5")

    obs, reward, done, info = env.step(req.action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info,
        "action_source": "manual",
    }


@app.post("/env/gemini-step")
def gemini_step(req: GeminiStepRequest):
    """
    Let the Gemini agent observe the current grid state and decide the
    next action, then advance the simulation.
    Automatically rotates API keys if quota is exhausted.
    """
    env = _envs.get(req.task)
    if env is None:
        raise HTTPException(status_code=404,
                            detail="Environment not found. Call /env/reset first.")

    key_manager = _init_key_manager()
    current_obs = env.state()
    
    max_retries = len(key_manager.api_keys)
    for attempt in range(max_retries):
        try:
            agent, _ = _get_gemini_agent()
            action = agent.predict(current_obs, verbose=False)
            
            obs, reward, done, info = env.step(action)
            return {
                "observation": obs,
                "reward": reward,
                "done": done,
                "info": info,
                "action": action,
                "action_source": "gemini",
                "api_key_rotation": {"attempt": attempt, "success": True},
            }
        
        except ApiKeyError as e:
            print(f"[ROTATE] API Key exhausted (attempt {attempt + 1}/{max_retries}): {e}")
            # Get current key before it's rotated
            current_key = key_manager.get_key()
            key_manager.mark_key_failed(current_key)

            if attempt == max_retries - 1:
                # Fallback to mock agent instead of returning 503
                print("[FALLBACK] All API keys exhausted, using mock agent")
                mock_agent = MockGeminiGridAgent()
                action = mock_agent.predict(current_obs)
                obs, reward, done, info = env.step(action)
                return {
                    "observation": obs,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "action": action,
                    "action_source": "mock (API keys exhausted)",
                    "api_key_rotation": {"attempt": attempt + 1, "success": False, "fallback": "mock"},
                }
        
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/env/state/{task}")
def get_state(task: str):
    """Return the current observation without advancing the simulation."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404,
                            detail="Environment not found. Call /env/reset first.")
    return {"observation": env.state()}


@app.get("/env/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "name": "Single City Grid",        "difficulty": 1},
            {"id": "medium", "name": "Multi-Region Grid",        "difficulty": 2},
            {"id": "hard",   "name": "Renewable Fluctuation",    "difficulty": 3},
        ]
    }


@app.get("/analytics/summary/{task}")
def analytics_summary(task: str):
    """Return a lightweight analytics summary for the current state."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404,
                            detail="Environment not found. Call /env/reset first.")
    obs = env.state()
    total_renewable = obs["solar_generation"] + obs["wind_generation"]
    renewable_pct = (total_renewable / obs["demand"] * 100) if obs["demand"] > 0 else 0
    return {
        "total_demand_mw": obs["demand"],
        "renewable_generation_mw": round(total_renewable, 2),
        "renewable_percentage": round(renewable_pct, 1),
        "battery_storage_pct": obs["battery_storage"],
        "transmission_load_pct": obs["transmission_load"],
        "grid_stability": "stable" if obs["transmission_load"] < 90 else "critical",
    }


# ---------------------------------------------------------------------------
# New Endpoints: Forecast, Risk, Stability, Topology, Scenarios, Recovery
# ---------------------------------------------------------------------------

@app.get("/forecast/{task}")
def get_forecast(task: str):
    """Return 24-hour renewable energy forecast based on solar/wind curves."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    sim = env._simulator
    current_hour = sim.time_of_day
    total_solar_cap = sum(r.solar_capacity for r in sim.regions)
    total_wind_cap = sum(r.wind_capacity for r in sim.regions)

    forecast = []
    for i in range(24):
        hour = (current_hour + i) % 24
        solar_factor = GridSimulator.SOLAR_CURVE[hour]
        wind_factor = 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)
        forecast.append({
            "hour": hour,
            "solar_mw": round(total_solar_cap * solar_factor, 1),
            "wind_mw": round(total_wind_cap * max(0, min(1, wind_factor)), 1),
        })

    return {"task": task, "current_hour": current_hour, "forecast": forecast}


@app.get("/blackout-risk/{task}")
def get_blackout_risk(task: str):
    """Return per-region blackout risk percentage."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    sim = env._simulator
    hour = sim.time_of_day
    solar_f = GridSimulator.SOLAR_CURVE[hour]
    wind_f = max(0, min(1, 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)))
    demand_f = GridSimulator.DEMAND_CURVE[hour]

    regions_risk = []
    for r in sim.regions:
        supply = (r.solar_capacity * solar_f +
                  r.wind_capacity * wind_f +
                  r.battery_charge * r.battery_capacity * 0.1)
        demand = r.base_demand * demand_f
        ratio = supply / demand if demand > 0 else 1.0
        risk = max(0, min(100, (1 - ratio) * 100))
        if r.has_backup_generator:
            risk = max(0, risk - 15)
        level = "green" if risk < 30 else "yellow" if risk < 60 else "red"
        regions_risk.append({
            "name": r.name,
            "risk_pct": round(risk, 1),
            "level": level,
        })

    return {"task": task, "regions": regions_risk}


@app.get("/stability/{task}")
def get_stability(task: str):
    """Return grid stability index (0-100) with component breakdown."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    obs = env.state()
    demand = obs["demand"]
    renewable = obs["solar_generation"] + obs["wind_generation"]

    transmission_score = max(0, 100 - obs["transmission_load"])
    supply_demand_score = min(100, (renewable / demand * 100)) if demand > 0 else 100
    battery_score = obs["battery_storage"]
    blackout_score = 100 if obs["transmission_load"] < 95 else 0

    index = (0.4 * transmission_score +
             0.3 * supply_demand_score +
             0.2 * battery_score +
             0.1 * blackout_score)

    label = "critical" if index < 30 else "warning" if index < 60 else "stable"

    return {
        "task": task,
        "stability_index": round(index, 1),
        "components": {
            "transmission": round(transmission_score, 1),
            "supply_demand": round(supply_demand_score, 1),
            "battery": round(battery_score, 1),
            "blackout_free": round(blackout_score, 1),
        },
        "label": label,
    }


# Hardcoded SVG layout coordinates per task
_TOPOLOGY_COORDS = {
    "easy": {
        "nodes": [
            {"id": "city-a", "type": "city", "label": "City A", "x": 300, "y": 200},
            {"id": "solar-a", "type": "solar", "label": "Solar Farm", "x": 140, "y": 100},
            {"id": "battery-a", "type": "battery", "label": "Storage", "x": 460, "y": 100},
            {"id": "gen-a", "type": "generator", "label": "Backup Gen", "x": 300, "y": 340},
        ],
        "edges": [
            {"from": "solar-a", "to": "city-a"},
            {"from": "battery-a", "to": "city-a"},
            {"from": "gen-a", "to": "city-a"},
        ],
    },
    "medium": {
        "nodes": [
            {"id": "city-a", "type": "city", "label": "Region A", "x": 150, "y": 200},
            {"id": "city-b", "type": "city", "label": "Region B", "x": 300, "y": 80},
            {"id": "city-c", "type": "city", "label": "Region C", "x": 450, "y": 200},
            {"id": "solar-a", "type": "solar", "label": "Solar A", "x": 60, "y": 90},
            {"id": "wind-b", "type": "wind", "label": "Wind B", "x": 230, "y": 10},
            {"id": "solar-c", "type": "solar", "label": "Solar C", "x": 530, "y": 90},
            {"id": "battery-a", "type": "battery", "label": "Storage A", "x": 60, "y": 310},
            {"id": "battery-b", "type": "battery", "label": "Storage B", "x": 300, "y": 340},
            {"id": "battery-c", "type": "battery", "label": "Storage C", "x": 530, "y": 310},
        ],
        "edges": [
            {"from": "solar-a", "to": "city-a"},
            {"from": "wind-b", "to": "city-b"},
            {"from": "solar-c", "to": "city-c"},
            {"from": "battery-a", "to": "city-a"},
            {"from": "battery-b", "to": "city-b"},
            {"from": "battery-c", "to": "city-c"},
            {"from": "city-a", "to": "city-b"},
            {"from": "city-b", "to": "city-c"},
            {"from": "city-a", "to": "city-c"},
        ],
    },
    "hard": {
        "nodes": [
            {"id": "city-a", "type": "city", "label": "Metro A", "x": 150, "y": 200},
            {"id": "city-b", "type": "city", "label": "Metro B", "x": 300, "y": 60},
            {"id": "city-c", "type": "city", "label": "Industrial C", "x": 450, "y": 200},
            {"id": "solar-a", "type": "solar", "label": "Solar A", "x": 50, "y": 80},
            {"id": "wind-a", "type": "wind", "label": "Wind A", "x": 50, "y": 280},
            {"id": "wind-b", "type": "wind", "label": "Wind B", "x": 220, "y": 10},
            {"id": "solar-b", "type": "solar", "label": "Solar B", "x": 400, "y": 10},
            {"id": "solar-c", "type": "solar", "label": "Solar C", "x": 550, "y": 100},
            {"id": "wind-c", "type": "wind", "label": "Wind C", "x": 550, "y": 300},
            {"id": "battery-a", "type": "battery", "label": "Storage A", "x": 150, "y": 340},
            {"id": "battery-b", "type": "battery", "label": "Storage B", "x": 300, "y": 340},
            {"id": "battery-c", "type": "battery", "label": "Storage C", "x": 450, "y": 340},
        ],
        "edges": [
            {"from": "solar-a", "to": "city-a"},
            {"from": "wind-a", "to": "city-a"},
            {"from": "wind-b", "to": "city-b"},
            {"from": "solar-b", "to": "city-b"},
            {"from": "solar-c", "to": "city-c"},
            {"from": "wind-c", "to": "city-c"},
            {"from": "battery-a", "to": "city-a"},
            {"from": "battery-b", "to": "city-b"},
            {"from": "battery-c", "to": "city-c"},
            {"from": "city-a", "to": "city-b"},
            {"from": "city-b", "to": "city-c"},
            {"from": "city-a", "to": "city-c"},
        ],
    },
}


@app.get("/grid-topology/{task}")
def get_grid_topology(task: str):
    """Return grid map node/edge data with live simulation values."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    topo = _TOPOLOGY_COORDS.get(task)
    if topo is None:
        raise HTTPException(status_code=400, detail=f"No topology for task: {task}")

    sim = env._simulator
    obs = env.state()
    hour = sim.time_of_day
    solar_f = GridSimulator.SOLAR_CURVE[hour]
    wind_f = max(0, min(1, 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)))
    demand_f = GridSimulator.DEMAND_CURVE[hour]

    # Build type-ordered index: for each type, the Nth node of that type maps to region N
    type_counters: Dict[str, int] = {}
    nodes = []
    for n in topo["nodes"]:
        node = dict(n)
        ntype = n["type"]
        idx = type_counters.get(ntype, 0)
        type_counters[ntype] = idx + 1

        if ntype == "city" and idx < len(sim.regions):
            r = sim.regions[idx]
            node["demand"] = round(r.base_demand * demand_f, 1)
            node["has_generator"] = r.has_backup_generator
        elif ntype == "solar" and idx < len(sim.regions):
            node["output"] = round(sim.regions[idx].solar_capacity * solar_f, 1)
            node["capacity"] = sim.regions[idx].solar_capacity
        elif ntype == "wind" and idx < len(sim.regions):
            node["output"] = round(sim.regions[idx].wind_capacity * wind_f, 1)
            node["capacity"] = sim.regions[idx].wind_capacity
        elif ntype == "battery" and idx < len(sim.regions):
            node["charge_pct"] = round(sim.regions[idx].battery_charge * 100, 1)
            node["capacity"] = sim.regions[idx].battery_capacity
        elif ntype == "generator" and idx < len(sim.regions):
            node["output"] = sim.regions[idx].generator_output
        nodes.append(node)

    edges = []
    for e in topo["edges"]:
        edge = dict(e)
        edge["flow_mw"] = round(obs["demand"] / max(1, len(topo["edges"])), 1)
        edges.append(edge)

    return {"task": task, "nodes": nodes, "edges": edges}


VALID_SCENARIOS = [
    "demand_surge", "solar_install", "wind_failure", "storm",
    "transmission_failure", "plant_shutdown", "renewable_collapse",
]

SCENARIO_DESCRIPTIONS = {
    "demand_surge": "Demand surge: +{pct}% load across all regions",
    "solar_install": "Solar installation: +{pct}% solar capacity",
    "wind_failure": "Wind turbine failure: -{pct}% wind capacity",
    "storm": "Storm conditions: -80% solar, +80% wind",
    "transmission_failure": "Transmission failure: -{pct}% grid capacity",
    "plant_shutdown": "Plant shutdown: backup generators offline",
    "renewable_collapse": "Renewable collapse: -{pct}% solar & wind",
}


@app.post("/scenario/inject")
def inject_scenario(req: ScenarioInjectRequest):
    """Inject a specific scenario into the simulation."""
    env = _envs.get(req.task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")
    if req.scenario not in VALID_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Choose from: {VALID_SCENARIOS}")

    sim = env._simulator
    intensity = max(0.5, min(2.0, req.intensity))

    # Store originals if not already stored
    if req.task not in _original_regions:
        _original_regions[req.task] = [
            copy.deepcopy(r) for r in sim.regions
        ]
        _active_scenarios[req.task] = {"scenario": req.scenario, "step": env._step_count}

    pct = int(intensity * 100)

    if req.scenario == "demand_surge":
        for r in sim.regions:
            r.base_demand *= (1.0 + 0.3 * intensity)
    elif req.scenario == "solar_install":
        for r in sim.regions:
            r.solar_capacity *= (1.0 + 0.5 * intensity)
    elif req.scenario == "wind_failure":
        for r in sim.regions:
            r.wind_capacity *= max(0.1, 1.0 - 0.7 * intensity)
    elif req.scenario == "storm":
        for r in sim.regions:
            r.solar_capacity *= 0.2
            r.wind_capacity *= 1.8
        # For hard task, also set storm flag
        if hasattr(sim, '_storm_active'):
            sim._storm_active = True
    elif req.scenario == "transmission_failure":
        sim.grid_capacity *= max(0.2, 1.0 - 0.5 * intensity)
    elif req.scenario == "plant_shutdown":
        for r in sim.regions:
            r.has_backup_generator = False
            r.generator_output = 0.0
    elif req.scenario == "renewable_collapse":
        for r in sim.regions:
            r.solar_capacity *= max(0.1, 1.0 - 0.7 * intensity)
            r.wind_capacity *= max(0.1, 1.0 - 0.7 * intensity)

    _active_scenarios[req.task] = {"scenario": req.scenario, "step": env._step_count}

    obs = env.state()
    msg = SCENARIO_DESCRIPTIONS.get(req.scenario, req.scenario).format(pct=pct)

    return {
        "task": req.task,
        "scenario": req.scenario,
        "applied": True,
        "observation": obs,
        "message": msg,
    }


@app.post("/scenario/clear")
def clear_scenario(req: ScenarioClearRequest):
    """Clear injected scenario and restore original region parameters."""
    env = _envs.get(req.task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    sim = env._simulator
    originals = _original_regions.pop(req.task, None)
    _active_scenarios.pop(req.task, None)

    if originals:
        for i, orig in enumerate(originals):
            if i < len(sim.regions):
                sim.regions[i] = orig
        # Restore grid capacity
        sim.grid_capacity = sum(
            r.solar_capacity + r.wind_capacity + r.generator_output
            for r in sim.regions
        )
        if hasattr(sim, '_storm_active'):
            sim._storm_active = False
            sim._demand_surge = False

    obs = env.state()
    return {"task": req.task, "cleared": True, "observation": obs}


@app.get("/recovery-status/{task}")
def get_recovery_status(task: str):
    """Return emergency recovery progress when a scenario is active."""
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")

    scenario_info = _active_scenarios.get(task)
    if not scenario_info:
        return {
            "task": task,
            "active_emergency": False,
            "scenario": None,
            "recovery_pct": 100,
            "steps_since_injection": 0,
            "stability_restored": True,
        }

    obs = env.state()
    demand = obs["demand"]
    renewable = obs["solar_generation"] + obs["wind_generation"]
    battery_contrib = obs["battery_storage"] / 100 * sum(
        r.battery_capacity for r in env._simulator.regions
    ) * 0.1

    total_supply = renewable + battery_contrib
    ratio = total_supply / demand if demand > 0 else 1.0
    recovery_pct = min(100, max(0, ratio * 100))
    steps_since = env._step_count - scenario_info.get("step", 0)
    stability_restored = recovery_pct >= 85

    return {
        "task": task,
        "active_emergency": True,
        "scenario": scenario_info["scenario"],
        "recovery_pct": round(recovery_pct, 1),
        "steps_since_injection": steps_since,
        "stability_restored": stability_restored,
    }
