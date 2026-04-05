"""
Grid Simulation Engine
Models real-world electricity grid components: cities/regions, renewable
energy plants, battery storage, transmission lines, and backup generators.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class Region:
    name: str
    base_demand: float          # MW
    solar_capacity: float       # MW
    wind_capacity: float        # MW
    battery_capacity: float     # MWh
    battery_charge: float       # 0.0 – 1.0
    has_backup_generator: bool
    generator_output: float     # MW (max)


@dataclass
class GridState:
    demand: float               # MW — total grid demand
    solar_generation: float     # MW
    wind_generation: float      # MW
    battery_storage: float      # percent 0–100
    grid_capacity: float        # MW
    transmission_load: float    # percent 0–100
    time_of_day: int            # 0–23
    region_demands: List[float] = field(default_factory=list)
    blackout: bool = False
    fossil_fuel_used: float = 0.0   # MW currently from generators
    energy_wasted: float = 0.0      # MW curtailed / overproduced


class GridSimulator:
    """Simulates a multi-region electricity grid."""

    SOLAR_CURVE = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.05,
        0.15, 0.35, 0.55, 0.75, 0.90, 0.98,
        1.00, 0.98, 0.90, 0.75, 0.55, 0.30,
        0.10, 0.0, 0.0, 0.0, 0.0, 0.0,
    ]

    DEMAND_CURVE = [
        0.55, 0.50, 0.48, 0.47, 0.48, 0.52,
        0.60, 0.70, 0.80, 0.85, 0.88, 0.90,
        0.88, 0.85, 0.83, 0.85, 0.90, 0.95,
        1.00, 0.98, 0.90, 0.80, 0.70, 0.62,
    ]

    def __init__(self, regions: List[Region], time_step_minutes: int = 60):
        self.regions = regions
        self.time_step_minutes = time_step_minutes
        self.time_of_day: int = 0
        self.step_count: int = 0
        self.grid_capacity: float = sum(r.solar_capacity + r.wind_capacity +
                                        r.generator_output for r in regions)
        self._rng = np.random.default_rng()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> GridState:
        self.time_of_day = 0
        self.step_count = 0
        for region in self.regions:
            region.battery_charge = 0.5
        return self._build_state()

    def step(self, action: int) -> GridState:
        """Advance simulation one time-step after applying the action."""
        self._apply_action(action)
        self._advance_time()
        return self._build_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _advance_time(self):
        self.step_count += 1
        self.time_of_day = (self.time_of_day + 1) % 24

    def _solar_factor(self) -> float:
        base = self.SOLAR_CURVE[self.time_of_day]
        noise = self._rng.normal(0, 0.05)
        return float(np.clip(base + noise, 0.0, 1.0))

    def _wind_factor(self) -> float:
        base = 0.4 + 0.3 * np.sin(self.time_of_day / 24 * 2 * np.pi)
        noise = self._rng.normal(0, 0.10)
        return float(np.clip(base + noise, 0.0, 1.0))

    def _demand_factor(self) -> float:
        base = self.DEMAND_CURVE[self.time_of_day]
        noise = self._rng.normal(0, 0.03)
        return float(np.clip(base + noise, 0.3, 1.2))

    def _apply_action(self, action: int):
        if action == 1:   # charge battery
            self._charge_batteries(fraction=0.10)
        elif action == 2: # discharge battery
            self._discharge_batteries(fraction=0.10)
        elif action == 3: # activate generator
            for r in self.regions:
                if r.has_backup_generator:
                    r.generator_output = min(r.generator_output * 1.1, 50.0)
        elif action == 4: # curtail renewable — no-op in simulator (tracked in reward)
            pass
        elif action in (0, 5): # redistribute — handled externally by reward engine
            pass

    def _charge_batteries(self, fraction: float):
        for r in self.regions:
            r.battery_charge = min(1.0, r.battery_charge + fraction)

    def _discharge_batteries(self, fraction: float):
        for r in self.regions:
            r.battery_charge = max(0.0, r.battery_charge - fraction)

    def _build_state(self) -> GridState:
        sf = self._solar_factor()
        wf = self._wind_factor()
        df = self._demand_factor()

        solar = sum(r.solar_capacity * sf for r in self.regions)
        wind = sum(r.wind_capacity * wf for r in self.regions)
        demand = sum(r.base_demand * df for r in self.regions)
        avg_battery = np.mean([r.battery_charge for r in self.regions]) * 100
        region_demands = [r.base_demand * df for r in self.regions]

        total_supply = solar + wind + avg_battery / 100 * sum(
            r.battery_capacity for r in self.regions
        ) * 0.1

        transmission_load = min(100.0, (demand / self.grid_capacity) * 100)
        blackout = total_supply < demand * 0.85
        fossil = sum(r.generator_output for r in self.regions
                     if r.has_backup_generator and total_supply < demand)
        waste = max(0.0, total_supply - demand)

        return GridState(
            demand=round(demand, 2),
            solar_generation=round(solar, 2),
            wind_generation=round(wind, 2),
            battery_storage=round(avg_battery, 2),
            grid_capacity=round(self.grid_capacity, 2),
            transmission_load=round(transmission_load, 2),
            time_of_day=self.time_of_day,
            region_demands=[round(d, 2) for d in region_demands],
            blackout=blackout,
            fossil_fuel_used=round(fossil, 2),
            energy_wasted=round(waste, 2),
        )
