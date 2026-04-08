"""
OpenEnv Client for VoltWise Energy Grid Environment.

Provides programmatic access to the environment server via HTTP.

Usage:
    from client import GridEnvClient
    from models import GridAction

    with GridEnvClient(base_url="http://localhost:8000").sync() as client:
        obs = client.reset()
        obs = client.step(GridAction(action=1))
        print(obs.demand, obs.solar_generation)
"""

from openenv.core.env_client import EnvClient
from models import GridAction, GridObservation


class GridEnvClient(EnvClient[GridAction, GridObservation]):
    """Client for the VoltWise Energy Grid OpenEnv environment."""

    def _parse_observation(self, data: dict) -> GridObservation:
        return GridObservation(**data)

    def _serialize_action(self, action: GridAction) -> dict:
        return action.model_dump()
