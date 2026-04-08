"""
OpenEnv Environment Implementation for VoltWise Energy Grid.

Implements the standard OpenEnv Environment interface (reset/step/state)
using the grid simulator and reward engine.
"""

import sys
import os
from typing import Any, Optional
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openenv.core.env_server import Environment
from models import GridAction, GridObservation, GridState
from grid_simulator import GridSimulator, Region
from reward_engine import RewardEngine


class EnergyGridEnvironment(Environment[GridAction, GridObservation, GridState]):
    """
    OpenEnv-compatible smart grid environment.

    The AI agent manages electricity distribution across a simulated
    power grid with renewable energy, battery storage, and backup generators.

    Actions (discrete, 6):
        0 → redirect_power
        1 → charge_battery
        2 → discharge_battery
        3 → activate_generator
        4 → curtail_renewable
        5 → redistribute_regional_power
    """

    MAX_STEPS = 168  # one simulated week at hourly resolution

    def __init__(self, task: str = "medium"):
        super().__init__()
        self.task = task
        self._simulator = self._build_simulator(task)
        self._reward_engine = RewardEngine()
        self._step_count = 0
        self._total_reward = 0.0
        self._episode_id: str = ""
        self._current_obs: Optional[GridObservation] = None

    # ------------------------------------------------------------------
    # OpenEnv API
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> GridObservation:
        """Reset the environment and return the initial observation."""
        self._episode_id = episode_id or str(uuid4())[:8]
        self._step_count = 0
        self._total_reward = 0.0

        if seed is not None:
            import numpy as np
            self._simulator._rng = np.random.default_rng(seed)

        grid_state = self._simulator.reset()
        self._current_obs = self._grid_state_to_obs(grid_state, reward=0.0, done=False)
        return self._current_obs

    def step(
        self,
        action: GridAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> GridObservation:
        """Apply action, advance simulation, return observation with reward."""
        action_id = action.action
        assert 0 <= action_id <= 5, f"Invalid action {action_id}"

        grid_state = self._simulator.step(action_id)
        breakdown = self._reward_engine.calculate(grid_state)
        self._step_count += 1
        self._total_reward += breakdown.total
        done = self._step_count >= self.MAX_STEPS

        obs = self._grid_state_to_obs(grid_state, reward=breakdown.total, done=done)
        obs.metadata = {
            "reward_breakdown": {
                "demand_reward": float(breakdown.demand_reward),
                "renewable_reward": float(breakdown.renewable_reward),
                "blackout_penalty": float(breakdown.blackout_penalty),
                "generator_penalty": float(breakdown.generator_penalty),
                "waste_penalty": float(breakdown.waste_penalty),
            },
            "step": self._step_count,
        }
        self._current_obs = obs
        return obs

    @property
    def state(self) -> GridState:
        """Get the current environment state."""
        return GridState(
            episode_id=self._episode_id,
            step_count=self._step_count,
            task=self.task,
            max_steps=self.MAX_STEPS,
            total_reward=round(self._total_reward, 2),
        )

    def get_metadata(self):
        from openenv.core.env_server.types import EnvironmentMetadata
        return EnvironmentMetadata(
            name="energy-grid-env",
            description="AI-powered smart grid simulation for reinforcement learning",
            version="2.0.0",
            author="VoltWise",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _grid_state_to_obs(gs, reward: float, done: bool) -> GridObservation:
        return GridObservation(
            done=done,
            reward=reward,
            demand=float(gs.demand),
            solar_generation=float(gs.solar_generation),
            wind_generation=float(gs.wind_generation),
            battery_storage=float(gs.battery_storage),
            grid_capacity=float(gs.grid_capacity),
            transmission_load=float(gs.transmission_load),
            time_of_day=int(gs.time_of_day),
            region_demands=[float(d) for d in gs.region_demands],
            blackout=bool(gs.blackout),
            fossil_fuel_used=float(gs.fossil_fuel_used),
            energy_wasted=float(gs.energy_wasted),
        )

    @staticmethod
    def _build_simulator(task: str) -> GridSimulator:
        if task == "easy":
            from tasks.easy import build_regions
            return GridSimulator(build_regions())
        elif task == "medium":
            from tasks.medium import build_regions
            return GridSimulator(build_regions())
        elif task == "hard":
            from tasks.hard import HardGridSimulator
            return HardGridSimulator()
        else:
            raise ValueError(f"Unknown task: {task}")
