"""
Reward Engine
Calculates per-step rewards to guide the RL agent toward optimal
grid management: satisfy demand, maximise renewables, avoid blackouts.
"""

from dataclasses import dataclass
from grid_simulator import GridState


@dataclass
class RewardBreakdown:
    demand_reward: float = 0.0
    renewable_reward: float = 0.0
    blackout_penalty: float = 0.0
    generator_penalty: float = 0.0
    waste_penalty: float = 0.0
    total: float = 0.0


class RewardEngine:
    """
    Reward design:
        +10  demand fully satisfied
        +5   renewable energy used (scaled by renewable fraction)
        -10  blackout detected
        -3   fossil fuel generators active
        -2   energy wasted (curtailed / overproduced)
    """

    DEMAND_REWARD = 10.0
    RENEWABLE_REWARD = 5.0
    BLACKOUT_PENALTY = -10.0
    GENERATOR_PENALTY = -3.0
    WASTE_PENALTY = -2.0

    def calculate(self, state: GridState) -> RewardBreakdown:
        rb = RewardBreakdown()

        # Demand satisfaction
        if not state.blackout:
            rb.demand_reward = self.DEMAND_REWARD

        # Renewable usage bonus — scaled by fraction of supply that is renewable
        total_supply = state.solar_generation + state.wind_generation
        if state.demand > 0:
            renewable_fraction = min(1.0, total_supply / state.demand)
            rb.renewable_reward = self.RENEWABLE_REWARD * renewable_fraction

        # Blackout penalty
        if state.blackout:
            rb.blackout_penalty = self.BLACKOUT_PENALTY

        # Fossil fuel penalty
        if state.fossil_fuel_used > 0:
            rb.generator_penalty = self.GENERATOR_PENALTY

        # Energy waste penalty (scaled, capped at -2)
        if state.energy_wasted > 0:
            waste_fraction = min(1.0, state.energy_wasted / max(state.demand, 1.0))
            rb.waste_penalty = self.WASTE_PENALTY * waste_fraction

        rb.total = (
            rb.demand_reward
            + rb.renewable_reward
            + rb.blackout_penalty
            + rb.generator_penalty
            + rb.waste_penalty
        )
        return rb
