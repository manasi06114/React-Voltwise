"""
Mock Agent Runner — Test training without Gemini API quota
Use this to test the full system when Gemini quota is exhausted.

Run:
    python agent/train_agent_mock.py --task medium --episodes 5 --verbose
    python agent/train_agent_mock.py --task hard --episodes 3
"""

import argparse
import sys
import os
from collections import deque
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env'))

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from env import EnergyGridEnv
from agent.mock_model import MockGeminiGridAgent


def run_episode(env: EnergyGridEnv, agent: MockGeminiGridAgent, verbose: bool) -> dict:
    """Run one full episode and return performance metrics."""
    obs = env.reset()
    done = False
    total_reward = 0.0
    steps = 0
    blackouts = 0
    fossil_steps = 0
    renewable_rewards = 0.0

    while not done:
        action = agent.predict(obs, verbose=verbose)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1

        if info.get("blackout"):
            blackouts += 1
        if info.get("fossil_fuel_used", 0) > 0:
            fossil_steps += 1
        renewable_rewards += info.get("reward_breakdown", {}).get("renewable_reward", 0)

        if verbose:
            print(
                f"  step={steps:3d} | action={action} | reward={reward:6.2f} "
                f"| blackout={info.get('blackout', False)} "
                f"| fossil={info.get('fossil_fuel_used', 0):.1f} MW"
            )

    return {
        "total_reward": total_reward,
        "steps": steps,
        "blackouts": blackouts,
        "fossil_steps": fossil_steps,
        "renewable_reward": renewable_rewards,
        "avg_reward": total_reward / steps if steps > 0 else 0,
    }


def run(task: str, episodes: int, verbose: bool = False):
    """Run multiple training episodes."""
    print(f"\nMOCK agent running on task='{task}' | model=MockGeminiGridAgent (no API calls!)")
    print("-" * 70)

    agent = MockGeminiGridAgent()
    metrics_history = deque(maxlen=episodes)

    for ep in range(1, episodes + 1):
        print(f"\nEpisode {ep}/{episodes}")
        env = EnergyGridEnv(task=task)
        metrics = run_episode(env, agent, verbose=verbose)
        metrics_history.append(metrics)

        print(
            f"✓ Episode {ep} complete | "
            f"reward={metrics['total_reward']:.2f} | "
            f"steps={metrics['steps']} | "
            f"blackouts={metrics['blackouts']} | "
            f"fossil_usage={metrics['fossil_steps']}"
        )

    # Summary
    avg_reward = sum(m["total_reward"] for m in metrics_history) / len(metrics_history)
    total_blackouts = sum(m["blackouts"] for m in metrics_history)

    print("\n" + "=" * 70)
    print(f"Summary: task={task} | episodes={episodes}")
    print(f"  Average reward:   {avg_reward:.2f}")
    print(f"  Total blackouts:  {total_blackouts}")
    print(f"  Avg fossil steps: {sum(m['fossil_steps'] for m in metrics_history) / len(metrics_history):.1f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Gemini Agent Training")
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    run(args.task, args.episodes, args.verbose)
