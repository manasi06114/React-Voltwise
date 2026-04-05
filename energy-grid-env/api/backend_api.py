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
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from env import EnergyGridEnv
from reward_engine import RewardEngine
from agent.model import GeminiGridAgent, ApiKeyError
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
            print(f"🔄 API Key exhausted (attempt {attempt + 1}/{max_retries}): {e}")
            # Get current key before it's rotated
            current_key = key_manager.get_key()
            key_manager.mark_key_failed(current_key)
            
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=503,
                    detail=f"All {len(key_manager.api_keys)} API keys are exhausted. Please try again later.",
                )
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
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
