"""
VoltWise — OpenEnv Inference Script

Demonstrates how to interact with the Energy Grid environment
using the standard OpenEnv API (reset/step/state).

Usage:
    python inference.py
    python inference.py --task hard --steps 50
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "energy-grid-env"))

from models import GridAction, GridObservation, GridState
from server.environment import EnergyGridEnvironment
from agent.mock_model import MockGeminiGridAgent


def run_inference(task: str = "medium", steps: int = 24, verbose: bool = True):
    """Run the OpenEnv environment with the mock AI agent."""

    # Create OpenEnv environment
    env = EnergyGridEnvironment(task=task)

    # Reset — standard OpenEnv API
    obs = env.reset(seed=42)
    print(f"=== VoltWise Energy Grid — Task: {task} ===")
    print(f"Initial state: demand={obs.demand:.1f} MW, "
          f"solar={obs.solar_generation:.1f} MW, "
          f"wind={obs.wind_generation:.1f} MW, "
          f"battery={obs.battery_storage:.1f}%")
    print()

    # Create agent
    agent = MockGeminiGridAgent()
    total_reward = 0.0
    blackouts = 0

    for i in range(steps):
        # Agent predicts action from observation
        obs_dict = {
            "demand": obs.demand,
            "solar_generation": obs.solar_generation,
            "wind_generation": obs.wind_generation,
            "battery_storage": obs.battery_storage,
            "grid_capacity": obs.grid_capacity,
            "transmission_load": obs.transmission_load,
            "time_of_day": obs.time_of_day,
            "region_demands": obs.region_demands,
        }
        action_id = agent.predict(obs_dict)

        # Step — standard OpenEnv API
        action = GridAction(action=action_id)
        obs = env.step(action)

        total_reward += obs.reward or 0
        if obs.blackout:
            blackouts += 1

        if verbose:
            print(f"Step {i+1:3d} | Action: {action_id} | "
                  f"Demand: {obs.demand:6.1f} MW | "
                  f"Renewable: {obs.solar_generation + obs.wind_generation:6.1f} MW | "
                  f"Battery: {obs.battery_storage:5.1f}% | "
                  f"Reward: {obs.reward:+7.2f} | "
                  f"{'BLACKOUT' if obs.blackout else 'OK'}")

        if obs.done:
            print(f"\nEpisode ended at step {i+1}")
            break

    # State — standard OpenEnv API
    state = env.state
    print(f"\n=== Results ===")
    print(f"Total reward: {total_reward:.2f}")
    print(f"Blackouts: {blackouts}/{steps}")
    print(f"Episode ID: {state.episode_id}")
    print(f"Steps taken: {state.step_count}")

    return total_reward


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoltWise OpenEnv Inference")
    parser.add_argument("--task", default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run_inference(task=args.task, steps=args.steps, verbose=not args.quiet)
