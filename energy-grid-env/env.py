"""
OpenEnv Environment — energy-grid-env
Implements the standardised reset() / step() / state() API.
"""

import numpy as np
from typing import Dict, Any, Tuple

from grid_simulator import GridSimulator, GridState, Region
from reward_engine import RewardEngine, RewardBreakdown


class EnergyGridEnv:
    """
    OpenEnv-compatible smart grid environment.

    Observation dict keys match openenv.yaml:
        demand, solar_generation, wind_generation, battery_storage,
        grid_capacity, transmission_load, time_of_day, region_demands

    Action space (discrete, 6 actions):
        0 → redirect_power
        1 → charge_battery
        2 → discharge_battery
        3 → activate_generator
        4 → curtail_renewable
        5 → redistribute_regional_power
    """

    N_ACTIONS = 6
    MAX_STEPS = 168   # one simulated week at hourly resolution

    def __init__(self, task: str = "medium"):
        self.task = task
        self._simulator = self._build_simulator(task)
        self._reward_engine = RewardEngine()
        self._step_count = 0
        self._current_state: GridState | None = None

    # ------------------------------------------------------------------
    # OpenEnv API
    # ------------------------------------------------------------------

    def reset(self) -> Dict[str, Any]:
        """Reset the environment and return the initial observation."""
        self._step_count = 0
        self._current_state = self._simulator.reset()
        return self._to_obs(self._current_state)

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, Dict]:
        """
        Apply action, advance simulation, return (obs, reward, done, info).
        """
        assert 0 <= action < self.N_ACTIONS, f"Invalid action {action}"

        self._current_state = self._simulator.step(action)
        breakdown: RewardBreakdown = self._reward_engine.calculate(self._current_state)
        self._step_count += 1
        done = self._step_count >= self.MAX_STEPS

        info = {
            "reward_breakdown": {
                "demand_reward": float(breakdown.demand_reward),
                "renewable_reward": float(breakdown.renewable_reward),
                "blackout_penalty": float(breakdown.blackout_penalty),
                "generator_penalty": float(breakdown.generator_penalty),
                "waste_penalty": float(breakdown.waste_penalty),
            },
            "blackout": bool(self._current_state.blackout),
            "fossil_fuel_used": float(self._current_state.fossil_fuel_used),
            "energy_wasted": float(self._current_state.energy_wasted),
            "step": int(self._step_count),
        }

        return self._to_obs(self._current_state), breakdown.total, done, info

    def state(self) -> Dict[str, Any]:
        """Return current observation without advancing the simulation."""
        if self._current_state is None:
            raise RuntimeError("Call reset() before state().")
        return self._to_obs(self._current_state)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_obs(gs: GridState) -> Dict[str, Any]:
        return {
            "demand": float(gs.demand),
            "solar_generation": float(gs.solar_generation),
            "wind_generation": float(gs.wind_generation),
            "battery_storage": float(gs.battery_storage),
            "grid_capacity": float(gs.grid_capacity),
            "transmission_load": float(gs.transmission_load),
            "time_of_day": int(gs.time_of_day),
            "region_demands": [float(d) for d in gs.region_demands],
        }

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

    def observation_space_shape(self) -> int:
        """Flat observation vector length (used by neural network input layer)."""
        obs = self.reset()
        flat = self._flatten_obs(obs)
        return len(flat)

    @staticmethod
    def _flatten_obs(obs: Dict[str, Any]) -> np.ndarray:
        scalars = [
            obs["demand"],
            obs["solar_generation"],
            obs["wind_generation"],
            obs["battery_storage"],
            obs["grid_capacity"],
            obs["transmission_load"],
            float(obs["time_of_day"]),
        ]
        return np.array(scalars + list(obs["region_demands"]), dtype=np.float32)
