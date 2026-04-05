"""
Mock Gemini Grid Agent (No API Calls)
For testing and development when quota is exhausted.

Use instead of GeminiGridAgent for testing without live API calls.
"""

import random


ACTION_DESCRIPTIONS = {
    0: "redirect_power       — Redirect electricity between regions",
    1: "charge_battery       — Store excess energy in batteries",
    2: "discharge_battery    — Release stored energy from batteries",
    3: "activate_generator   — Activate fossil fuel backup generator (last resort)",
    4: "curtail_renewable    — Curtail excess renewable generation to prevent waste",
    5: "redistribute_power   — Redistribute power evenly across all regions",
}


class MockGeminiGridAgent:
    """
    Mock agent that simulates Gemini responses without API calls.
    Perfect for testing and development when quota is exhausted.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize mock agent (API key not used)."""
        pass

    def predict(self, obs: dict, verbose: bool = False) -> int:
        """
        Given a grid observation dict, return an intelligent action (0–5).
        Uses heuristic logic instead of Gemini API.
        """
        demand = obs.get("demand", 100)
        solar = obs.get("solar_generation", 0)
        wind = obs.get("wind_generation", 0)
        battery = obs.get("battery_storage", 50)
        
        renewable = solar + wind
        deficit = max(0, demand - renewable)
        
        # Smart heuristic logic
        if verbose:
            print(f"  [Mock] demand={demand:.1f}, renewable={renewable:.1f}, battery={battery:.1f}%")
        
        # Priority 1: If not enough energy, discharge battery or activate generator
        if deficit > 10:
            if battery > 30:
                action = 2  # Discharge battery
                reason = "Discharging battery to cover demand deficit"
            else:
                action = 3  # Activate generator
                reason = "Activating backup generator (battery low)"
        
        # Priority 2: If lots of renewable, charge battery
        elif renewable > demand + 20 and battery < 80:
            action = 1
            reason = "Charging battery with excess renewables"
        
        # Priority 3: If battery full and still excess, curtail
        elif renewable > demand + 10 and battery >= 90:
            action = 4
            reason = "Curtailing excess renewable generation"
        
        # Priority 4: Balance across regions
        else:
            action = 5
            reason = "Redistributing power for better balance"
        
        if verbose:
            print(f"  [Mock] action={action}: {ACTION_DESCRIPTIONS[action]}")
            print(f"  [Mock] reason: {reason}")
        
        return action
