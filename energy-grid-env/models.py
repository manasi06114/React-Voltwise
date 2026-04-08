"""
OpenEnv Pydantic Models for VoltWise Energy Grid Environment.

Defines the Action, Observation, and State types following the
OpenEnv specification from Meta/HuggingFace.
"""

from typing import List, Dict, Any
from pydantic import Field, ConfigDict
from openenv.core.env_server.types import Action, Observation, State


class GridAction(Action):
    """Discrete action for the energy grid environment.

    Actions:
        0 → redirect_power
        1 → charge_battery
        2 → discharge_battery
        3 → activate_generator
        4 → curtail_renewable
        5 → redistribute_regional_power
    """
    model_config = ConfigDict(extra="allow")

    action: int = Field(
        ..., ge=0, le=5,
        description="Discrete action ID (0-5)",
    )


class GridObservation(Observation):
    """Observation from the energy grid environment.

    Inherits done, reward, metadata from OpenEnv Observation base.
    """
    model_config = ConfigDict(extra="allow")

    demand: float = Field(default=0.0, description="Total grid demand in MW")
    solar_generation: float = Field(default=0.0, description="Solar generation in MW")
    wind_generation: float = Field(default=0.0, description="Wind generation in MW")
    battery_storage: float = Field(default=0.0, description="Battery charge level 0-100%")
    grid_capacity: float = Field(default=0.0, description="Total grid capacity in MW")
    transmission_load: float = Field(default=0.0, description="Transmission load 0-100%")
    time_of_day: int = Field(default=0, description="Hour of day 0-23")
    region_demands: List[float] = Field(default_factory=list, description="Per-region demand in MW")
    blackout: bool = Field(default=False, description="Whether a blackout is occurring")
    fossil_fuel_used: float = Field(default=0.0, description="Fossil fuel generation in MW")
    energy_wasted: float = Field(default=0.0, description="Energy wasted/curtailed in MW")


class GridState(State):
    """Episode state for the energy grid environment.

    Inherits episode_id and step_count from OpenEnv State base.
    """
    model_config = ConfigDict(extra="allow")

    task: str = Field(default="medium", description="Current task difficulty")
    max_steps: int = Field(default=168, description="Maximum steps per episode")
    total_reward: float = Field(default=0.0, description="Cumulative reward this episode")
