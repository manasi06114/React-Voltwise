"""
Hard Task — Renewable Fluctuation Scenario
Weather fluctuations, sudden solar drops, wind spikes, demand surges.
Goal: maintain grid stability despite unpredictable conditions.
"""

import numpy as np
from grid_simulator import Region, GridSimulator


def build_regions():
    """Larger multi-region grid with volatile renewable mix."""
    return [
        Region(
            name="Metro-A",
            base_demand=150.0,
            solar_capacity=100.0,
            wind_capacity=60.0,
            battery_capacity=80.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=50.0,
        ),
        Region(
            name="Metro-B",
            base_demand=120.0,
            solar_capacity=50.0,
            wind_capacity=90.0,
            battery_capacity=60.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=40.0,
        ),
        Region(
            name="Industrial-C",
            base_demand=200.0,
            solar_capacity=40.0,
            wind_capacity=30.0,
            battery_capacity=100.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=80.0,
        ),
    ]


class HardGridSimulator(GridSimulator):
    """Extends GridSimulator with weather event injection."""

    def __init__(self):
        super().__init__(build_regions())
        self._storm_active = False
        self._demand_surge = False

    def step(self, action):
        # Randomly trigger weather events
        rng = np.random.default_rng()
        if rng.random() < 0.05:
            self._storm_active = not self._storm_active
        if rng.random() < 0.03:
            self._demand_surge = not self._demand_surge
        return super().step(action)

    def _solar_factor(self):
        factor = super()._solar_factor()
        if self._storm_active:
            factor *= 0.2   # 80 % drop during storm
        return factor

    def _wind_factor(self):
        factor = super()._wind_factor()
        if self._storm_active:
            factor = min(1.0, factor * 1.8)   # wind spike
        return factor

    def _demand_factor(self):
        factor = super()._demand_factor()
        if self._demand_surge:
            factor *= 1.3   # 30 % demand surge
        return factor
