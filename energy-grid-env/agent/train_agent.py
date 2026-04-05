"""
Gemini Agent Runner — energy-grid-env
Runs evaluation episodes where the Gemini agent decides every action.

Install: pip install google-genai
Set:     export GEMINI_API_KEY=your_key_here

Run:
    python agent/train_agent.py --task medium --episodes 5
    python agent/train_agent.py --task hard   --episodes 3 --verbose
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
from agent.model import GeminiGridAgent


def run_episode(env: EnergyGridEnv, agent: GeminiGridAgent, verbose: bool) -> dict:
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
        "renewable_reward_total": renewable_rewards,
    }


def run(task: str = "medium", episodes: int = 5, verbose: bool = False):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    env = EnergyGridEnv(task=task)
    agent = GeminiGridAgent(api_key=api_key)
    reward_window = deque(maxlen=episodes)

    print(f"Gemini agent running on task='{task}' | model=gemini-3-flash-preview | thinking=HIGH")
    print("-" * 70)

    for ep in range(1, episodes + 1):
        print(f"\nEpisode {ep}/{episodes}")
        metrics = run_episode(env, agent, verbose=verbose)
        reward_window.append(metrics["total_reward"])

        print(
            f"  total_reward={metrics['total_reward']:8.2f} | "
            f"blackouts={metrics['blackouts']:3d} | "
            f"fossil_steps={metrics['fossil_steps']:3d} | "
            f"renewable_reward={metrics['renewable_reward_total']:.2f}"
        )

    avg = sum(reward_window) / len(reward_window)
    print("\n" + "=" * 70)
    print(f"Average reward over {episodes} episode(s): {avg:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Gemini grid agent")
    parser.add_argument("--task",     default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--verbose",  action="store_true", help="Print each step + Gemini response")
    args = parser.parse_args()
    run(args.task, args.episodes, args.verbose)
