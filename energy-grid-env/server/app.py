"""
FastAPI Application for VoltWise Energy Grid Environment.

Uses OpenEnv's create_fastapi_app() for standard reset/step/state routes,
then adds custom routes for forecast, risk, stability, topology,
scenarios, and Gemini AI integration.

Run:
    cd energy-grid-env
    python -m uvicorn server.app:app --port 8000
"""

import sys
import os
import math
import copy
from typing import Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openenv.core.env_server.http_server import create_fastapi_app
from models import GridAction, GridObservation, GridState
from server.environment import EnergyGridEnvironment
from grid_simulator import GridSimulator
from reward_engine import RewardEngine
from agent.model import GeminiGridAgent, ApiKeyError
from agent.mock_model import MockGeminiGridAgent
from api.key_manager import get_key_manager


# ---------------------------------------------------------------------------
# Create OpenEnv app (provides /reset, /step, /state, /health, /schema)
# ---------------------------------------------------------------------------

# Default environment factory (medium task)
def _env_factory():
    return EnergyGridEnvironment(task="medium")

app = create_fastapi_app(
    env=_env_factory,
    action_cls=GridAction,
    observation_cls=GridObservation,
)

app.title = "VoltWise - Energy Grid API (OpenEnv)"
app.description = "Smart Grid simulation powered by OpenEnv + Gemini AI"
app.version = "3.0.0"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Per-task environment store (for multi-task support beyond OpenEnv defaults)
# ---------------------------------------------------------------------------

_envs: Dict[str, EnergyGridEnvironment] = {}
_original_regions: Dict[str, list] = {}
_active_scenarios: Dict[str, dict] = {}
_key_manager = None
_gemini_agent = None


def _get_env(task: str) -> EnergyGridEnvironment:
    env = _envs.get(task)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found. Call /env/reset first.")
    return env


def _init_key_manager():
    global _key_manager
    if _key_manager is None:
        _key_manager = get_key_manager()
    return _key_manager


def _get_gemini_agent():
    global _gemini_agent
    km = _init_key_manager()
    api_key = km.get_key()
    _gemini_agent = GeminiGridAgent(api_key=api_key)
    return _gemini_agent, km


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class TaskRequest(BaseModel):
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
# Custom Routes — Multi-task environment management
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "VoltWise Energy Grid API (OpenEnv)",
        "version": "3.0.0",
        "framework": "OpenEnv by Meta/HuggingFace",
        "features": ["OpenEnv Standard API", "Multi-Task Support", "Gemini AI", "API Key Rotation"],
    }


@app.post("/env/reset")
def reset_env(req: TaskRequest):
    """Reset or create an environment for the given task."""
    if req.task not in ("easy", "medium", "hard"):
        raise HTTPException(status_code=400, detail=f"Unknown task: {req.task}")
    env = EnergyGridEnvironment(task=req.task)
    _envs[req.task] = env
    obs = env.reset()
    return {
        "task": req.task,
        "observation": obs.model_dump(),
        "step": 0,
        "session_id": req.task,
    }


@app.post("/env/step")
def step_env(req: StepRequest):
    """Apply a manual action and advance the simulation."""
    env = _get_env(req.task)
    if not (0 <= req.action <= 5):
        raise HTTPException(status_code=400, detail="action must be 0-5")

    action = GridAction(action=req.action)
    obs = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
        "info": {
            **obs.metadata,
            "blackout": obs.blackout,
            "fossil_fuel_used": obs.fossil_fuel_used,
            "energy_wasted": obs.energy_wasted,
        },
        "action_source": "manual",
    }


@app.post("/env/gemini-step")
def gemini_step(req: GeminiStepRequest):
    """Let Gemini AI decide the next action with automatic key rotation."""
    env = _get_env(req.task)
    km = _init_key_manager()

    # Build plain dict observation for the agent prompt
    current_obs = env._current_obs
    obs_dict = {
        "demand": current_obs.demand,
        "solar_generation": current_obs.solar_generation,
        "wind_generation": current_obs.wind_generation,
        "battery_storage": current_obs.battery_storage,
        "grid_capacity": current_obs.grid_capacity,
        "transmission_load": current_obs.transmission_load,
        "time_of_day": current_obs.time_of_day,
        "region_demands": current_obs.region_demands,
    }

    max_retries = len(km.api_keys)
    for attempt in range(max_retries):
        try:
            agent, _ = _get_gemini_agent()
            action_id = agent.predict(obs_dict, verbose=False)
            action = GridAction(action=action_id)
            obs = env.step(action)
            return {
                "observation": obs.model_dump(),
                "reward": obs.reward,
                "done": obs.done,
                "info": {
                    **obs.metadata,
                    "blackout": obs.blackout,
                    "fossil_fuel_used": obs.fossil_fuel_used,
                    "energy_wasted": obs.energy_wasted,
                },
                "action": action_id,
                "action_source": "gemini",
                "api_key_rotation": {"attempt": attempt, "success": True},
            }
        except ApiKeyError as e:
            print(f"[ROTATE] API Key exhausted (attempt {attempt + 1}/{max_retries}): {e}")
            current_key = km.get_key()
            km.mark_key_failed(current_key)

            if attempt == max_retries - 1:
                print("[FALLBACK] Using mock agent")
                mock = MockGeminiGridAgent()
                action_id = mock.predict(obs_dict)
                action = GridAction(action=action_id)
                obs = env.step(action)
                return {
                    "observation": obs.model_dump(),
                    "reward": obs.reward,
                    "done": obs.done,
                    "info": {
                        **obs.metadata,
                        "blackout": obs.blackout,
                        "fossil_fuel_used": obs.fossil_fuel_used,
                        "energy_wasted": obs.energy_wasted,
                    },
                    "action": action_id,
                    "action_source": "mock (API keys exhausted)",
                    "api_key_rotation": {"attempt": attempt + 1, "success": False, "fallback": "mock"},
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/env/state/{task}")
def get_env_state(task: str):
    env = _get_env(task)
    obs = env._current_obs
    return {"observation": obs.model_dump() if obs else {}}


@app.get("/env/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "name": "Single City Grid",     "difficulty": 1},
            {"id": "medium", "name": "Multi-Region Grid",     "difficulty": 2},
            {"id": "hard",   "name": "Renewable Fluctuation", "difficulty": 3},
        ]
    }


@app.get("/api-keys/status")
def api_key_status():
    try:
        km = _init_key_manager()
        return km.get_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# Analytics & Forecast endpoints
# ---------------------------------------------------------------------------

@app.get("/analytics/summary/{task}")
def analytics_summary(task: str):
    env = _get_env(task)
    obs = env._current_obs
    total_renewable = obs.solar_generation + obs.wind_generation
    renewable_pct = (total_renewable / obs.demand * 100) if obs.demand > 0 else 0
    return {
        "total_demand_mw": obs.demand,
        "renewable_generation_mw": round(total_renewable, 2),
        "renewable_percentage": round(renewable_pct, 1),
        "battery_storage_pct": obs.battery_storage,
        "transmission_load_pct": obs.transmission_load,
        "grid_stability": "stable" if obs.transmission_load < 90 else "critical",
    }


@app.get("/forecast/{task}")
def get_forecast(task: str):
    env = _get_env(task)
    sim = env._simulator
    current_hour = sim.time_of_day
    total_solar_cap = sum(r.solar_capacity for r in sim.regions)
    total_wind_cap = sum(r.wind_capacity for r in sim.regions)

    forecast = []
    for i in range(24):
        hour = (current_hour + i) % 24
        solar_f = GridSimulator.SOLAR_CURVE[hour]
        wind_f = 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)
        forecast.append({
            "hour": hour,
            "solar_mw": round(total_solar_cap * solar_f, 1),
            "wind_mw": round(total_wind_cap * max(0, min(1, wind_f)), 1),
        })
    return {"task": task, "current_hour": current_hour, "forecast": forecast}


@app.get("/blackout-risk/{task}")
def get_blackout_risk(task: str):
    env = _get_env(task)
    sim = env._simulator
    hour = sim.time_of_day
    solar_f = GridSimulator.SOLAR_CURVE[hour]
    wind_f = max(0, min(1, 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)))
    demand_f = GridSimulator.DEMAND_CURVE[hour]

    regions_risk = []
    for r in sim.regions:
        supply = r.solar_capacity * solar_f + r.wind_capacity * wind_f + r.battery_charge * r.battery_capacity * 0.1
        demand = r.base_demand * demand_f
        ratio = supply / demand if demand > 0 else 1.0
        risk = max(0, min(100, (1 - ratio) * 100))
        if r.has_backup_generator:
            risk = max(0, risk - 15)
        level = "green" if risk < 30 else "yellow" if risk < 60 else "red"
        regions_risk.append({"name": r.name, "risk_pct": round(risk, 1), "level": level})
    return {"task": task, "regions": regions_risk}


@app.get("/stability/{task}")
def get_stability(task: str):
    env = _get_env(task)
    obs = env._current_obs
    demand = obs.demand
    renewable = obs.solar_generation + obs.wind_generation

    t_score = max(0, 100 - obs.transmission_load)
    sd_score = min(100, (renewable / demand * 100)) if demand > 0 else 100
    b_score = obs.battery_storage
    bl_score = 100 if obs.transmission_load < 95 else 0

    index = 0.4 * t_score + 0.3 * sd_score + 0.2 * b_score + 0.1 * bl_score
    label = "critical" if index < 30 else "warning" if index < 60 else "stable"
    return {
        "task": task,
        "stability_index": round(index, 1),
        "components": {
            "transmission": round(t_score, 1),
            "supply_demand": round(sd_score, 1),
            "battery": round(b_score, 1),
            "blackout_free": round(bl_score, 1),
        },
        "label": label,
    }


# ---------------------------------------------------------------------------
# Grid topology — Real Pune, India coordinates (lat/lng)
# ---------------------------------------------------------------------------

_PUNE_TOPOLOGY = {
    "nodes": [
        # Cities / Load Centers
        {"id": "city-a", "type": "city", "label": "Pune Central", "lat": 18.5204, "lng": 73.8567},
        {"id": "city-b", "type": "city", "label": "Hinjewadi IT Hub", "lat": 18.5912, "lng": 73.7390},
        {"id": "city-c", "type": "city", "label": "Pimpri-Chinchwad", "lat": 18.6298, "lng": 73.7997},
        # Solar Farms
        {"id": "solar-a", "type": "solar", "label": "Saswad Solar Farm", "lat": 18.3456, "lng": 74.0312},
        {"id": "solar-b", "type": "solar", "label": "Daund Solar Park", "lat": 18.4632, "lng": 74.0890},
        {"id": "solar-c", "type": "solar", "label": "Uruli Solar Array", "lat": 18.4350, "lng": 73.9580},
        # Wind Farms
        {"id": "wind-a", "type": "wind", "label": "Sinhagad Wind Farm", "lat": 18.3667, "lng": 73.7558},
        {"id": "wind-b", "type": "wind", "label": "Bhor Wind Farm", "lat": 18.1534, "lng": 73.8478},
        {"id": "wind-c", "type": "wind", "label": "Mulshi Wind Farm", "lat": 18.5100, "lng": 73.5100},
        # Battery Storage
        {"id": "battery-a", "type": "battery", "label": "Wagholi Storage", "lat": 18.5803, "lng": 73.9787},
        {"id": "battery-b", "type": "battery", "label": "Hadapsar Storage", "lat": 18.5089, "lng": 73.9260},
        {"id": "battery-c", "type": "battery", "label": "Kothrud Storage", "lat": 18.5074, "lng": 73.8077},
        # Backup Generators
        {"id": "gen-a", "type": "generator", "label": "PCMC Power Plant", "lat": 18.6440, "lng": 73.8105},
        {"id": "gen-b", "type": "generator", "label": "Manjri Thermal", "lat": 18.5150, "lng": 73.9750},
    ],
    "edges": [
        # Solar → Cities
        {"from": "solar-a", "to": "city-a"}, {"from": "solar-b", "to": "city-b"},
        {"from": "solar-c", "to": "city-c"},
        # Wind → Cities
        {"from": "wind-a", "to": "city-a"}, {"from": "wind-b", "to": "city-a"},
        {"from": "wind-c", "to": "city-b"},
        # Battery → Cities
        {"from": "battery-a", "to": "city-a"}, {"from": "battery-b", "to": "city-c"},
        {"from": "battery-c", "to": "city-b"},
        # Generators → Cities
        {"from": "gen-a", "to": "city-c"}, {"from": "gen-b", "to": "city-a"},
        # City-to-City transmission
        {"from": "city-a", "to": "city-b"}, {"from": "city-b", "to": "city-c"},
        {"from": "city-a", "to": "city-c"},
    ],
    # Region boundaries for heatmap overlay (simplified polygon corners)
    "regions": [
        {"id": "city-a", "bounds": [[18.48, 73.82], [18.48, 73.90], [18.56, 73.90], [18.56, 73.82]]},
        {"id": "city-b", "bounds": [[18.56, 73.70], [18.56, 73.78], [18.62, 73.78], [18.62, 73.70]]},
        {"id": "city-c", "bounds": [[18.60, 73.76], [18.60, 73.84], [18.66, 73.84], [18.66, 73.76]]},
    ],
}

# Map all tasks to the same Pune topology (different difficulty = same city, different sim params)
_TOPOLOGY = {"easy": _PUNE_TOPOLOGY, "medium": _PUNE_TOPOLOGY, "hard": _PUNE_TOPOLOGY}


@app.get("/grid-topology/{task}")
def get_grid_topology(task: str):
    env = _get_env(task)
    topo = _TOPOLOGY.get(task)
    if not topo:
        raise HTTPException(status_code=400, detail=f"No topology for task: {task}")

    sim = env._simulator
    hour = sim.time_of_day
    solar_f = GridSimulator.SOLAR_CURVE[hour]
    wind_f = max(0, min(1, 0.4 + 0.3 * math.sin(hour / 24 * 2 * math.pi)))
    demand_f = GridSimulator.DEMAND_CURVE[hour]

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
            supply = r.solar_capacity * solar_f + r.wind_capacity * wind_f + r.battery_charge * r.battery_capacity * 0.1
            node["supply"] = round(supply, 1)
            node["has_generator"] = r.has_backup_generator
            node["status"] = "surplus" if supply >= r.base_demand * demand_f else "deficit"
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

    total_demand = env._current_obs.demand if env._current_obs else 1
    edges = [dict(e, flow_mw=round(total_demand / max(1, len(topo["edges"])), 1)) for e in topo["edges"]]

    # Region supply/demand for heatmap overlay
    regions = []
    for i, reg_info in enumerate(topo.get("regions", [])):
        if i < len(sim.regions):
            r = sim.regions[i]
            supply = r.solar_capacity * solar_f + r.wind_capacity * wind_f + r.battery_charge * r.battery_capacity * 0.1
            demand = r.base_demand * demand_f
            ratio = supply / demand if demand > 0 else 1.0
            color = "#22c55e" if ratio >= 0.9 else "#f59e0b" if ratio >= 0.6 else "#ef4444"
            regions.append({
                **reg_info,
                "supply": round(supply, 1),
                "demand": round(demand, 1),
                "ratio": round(ratio, 2),
                "color": color,
            })

    return {"task": task, "nodes": nodes, "edges": edges, "regions": regions}


# ---------------------------------------------------------------------------
# Scenario injection & Emergency recovery
# ---------------------------------------------------------------------------

VALID_SCENARIOS = [
    "demand_surge", "solar_install", "wind_failure", "storm",
    "transmission_failure", "plant_shutdown", "renewable_collapse",
    # Natural disasters
    "flood", "heavy_rain", "heatwave", "cyclone",
    "equipment_failure", "grid_overload", "solar_eclipse", "night_peak",
]

# Disaster effect definitions: {solar_mult, wind_mult, demand_mult, transmission_mult, generator_off}
DISASTER_EFFECTS = {
    "flood":              {"solar": 0.1, "wind": 1.0, "demand": 1.2, "transmission": 0.4, "gen_off": False},
    "heavy_rain":         {"solar": 0.3, "wind": 1.4, "demand": 1.0, "transmission": 0.8, "gen_off": False},
    "heatwave":           {"solar": 1.1, "wind": 0.6, "demand": 1.5, "transmission": 0.9, "gen_off": False},
    "cyclone":            {"solar": 0.0, "wind": 0.0, "demand": 0.8, "transmission": 0.2, "gen_off": True},
    "equipment_failure":  {"solar": 1.0, "wind": 1.0, "demand": 1.0, "transmission": 1.0, "gen_off": True},
    "grid_overload":      {"solar": 1.0, "wind": 1.0, "demand": 1.8, "transmission": 0.7, "gen_off": False},
    "solar_eclipse":      {"solar": 0.05, "wind": 1.0, "demand": 1.0, "transmission": 1.0, "gen_off": False},
    "night_peak":         {"solar": 0.0, "wind": 0.8, "demand": 1.4, "transmission": 0.9, "gen_off": False},
}


@app.post("/scenario/inject")
def inject_scenario(req: ScenarioInjectRequest):
    env = _get_env(req.task)
    if req.scenario not in VALID_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Choose from: {VALID_SCENARIOS}")

    sim = env._simulator
    intensity = max(0.5, min(2.0, req.intensity))

    if req.task not in _original_regions:
        _original_regions[req.task] = [copy.deepcopy(r) for r in sim.regions]

    # Check if this is a predefined disaster with effects
    effects = DISASTER_EFFECTS.get(req.scenario)
    if effects:
        for r in sim.regions:
            r.solar_capacity *= max(0.01, effects["solar"])
            r.wind_capacity *= max(0.01, effects["wind"])
            r.base_demand *= effects["demand"]
            if effects["gen_off"]:
                r.has_backup_generator = False
                r.generator_output = 0.0
        sim.grid_capacity *= max(0.1, effects["transmission"])
    elif req.scenario == "demand_surge":
        for r in sim.regions: r.base_demand *= (1.0 + 0.3 * intensity)
    elif req.scenario == "solar_install":
        for r in sim.regions: r.solar_capacity *= (1.0 + 0.5 * intensity)
    elif req.scenario == "wind_failure":
        for r in sim.regions: r.wind_capacity *= max(0.1, 1.0 - 0.7 * intensity)
    elif req.scenario == "storm":
        for r in sim.regions:
            r.solar_capacity *= 0.2
            r.wind_capacity *= 1.8
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
    obs = env._current_obs
    return {
        "task": req.task, "scenario": req.scenario, "applied": True,
        "observation": obs.model_dump() if obs else {},
        "message": f"Scenario '{req.scenario}' applied with intensity {intensity}",
    }


@app.post("/scenario/clear")
def clear_scenario(req: ScenarioClearRequest):
    env = _get_env(req.task)
    sim = env._simulator
    originals = _original_regions.pop(req.task, None)
    _active_scenarios.pop(req.task, None)

    if originals:
        for i, orig in enumerate(originals):
            if i < len(sim.regions):
                sim.regions[i] = orig
        sim.grid_capacity = sum(r.solar_capacity + r.wind_capacity + r.generator_output for r in sim.regions)
        if hasattr(sim, '_storm_active'):
            sim._storm_active = False
            sim._demand_surge = False

    obs = env._current_obs
    return {"task": req.task, "cleared": True, "observation": obs.model_dump() if obs else {}}


@app.get("/recovery-status/{task}")
def get_recovery_status(task: str):
    env = _get_env(task)
    scenario_info = _active_scenarios.get(task)
    if not scenario_info:
        return {"task": task, "active_emergency": False, "scenario": None,
                "recovery_pct": 100, "steps_since_injection": 0, "stability_restored": True}

    obs = env._current_obs
    renewable = obs.solar_generation + obs.wind_generation
    battery_contrib = obs.battery_storage / 100 * sum(r.battery_capacity for r in env._simulator.regions) * 0.1
    total_supply = renewable + battery_contrib
    ratio = total_supply / obs.demand if obs.demand > 0 else 1.0
    recovery_pct = min(100, max(0, ratio * 100))
    steps_since = env._step_count - scenario_info.get("step", 0)

    return {
        "task": task, "active_emergency": True, "scenario": scenario_info["scenario"],
        "recovery_pct": round(recovery_pct, 1), "steps_since_injection": steps_since,
        "stability_restored": recovery_pct >= 85,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
