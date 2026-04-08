"""
Grid Agent Runner
Runs evaluation episodes where the AI agent decides every action.

Run:
    cd energy-grid-env
    python agent/train_agent.py --task medium --episodes 5
    python agent/train_agent.py --task hard --episodes 3 --verbose
"""

import argparse
import sys
import os
from collections import deque
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from env import EnergyGridEnv
from agent.model import GeminiGridAgent


def run_episode(env, agent, verbose):
    obs = env.reset()
    done = False
    total_reward = 0.0
    steps = 0
    blackouts = 0
    fossil_steps = 0

    while not done:
        action = agent.predict(obs, verbose=verbose)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        if info.get("blackout"):
            blackouts += 1
        if info.get("fossil_fuel_used", 0) > 0:
            fossil_steps += 1
        if verbose:
            print(f"  step={steps:3d} | action={action} | reward={reward:6.2f} | blackout={info.get('blackout')}")

    return {"total_reward": total_reward, "steps": steps, "blackouts": blackouts, "fossil_steps": fossil_steps}


def run(task="medium", episodes=5, verbose=False):
    keys = os.environ.get("GEMINI_API_KEYS", "")
    api_key = keys.split(",")[0].strip() if keys else os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: No API key found. Set GEMINI_API_KEYS in .env")
        sys.exit(1)

    env = EnergyGridEnv(task=task)
    agent = GeminiGridAgent(api_key=api_key)
    reward_window = deque(maxlen=episodes)

    print(f"Agent running on task='{task}' | model=gemini-2.0-flash | OpenAI SDK")
    print("-" * 60)

    for ep in range(1, episodes + 1):
        print(f"\nEpisode {ep}/{episodes}")
        metrics = run_episode(env, agent, verbose)
        reward_window.append(metrics["total_reward"])
        print(f"  reward={metrics['total_reward']:8.2f} | blackouts={metrics['blackouts']:3d} | fossil={metrics['fossil_steps']:3d}")

    avg = sum(reward_window) / len(reward_window)
    print(f"\nAverage reward over {episodes} episode(s): {avg:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the grid agent")
    parser.add_argument("--task", default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    run(args.task, args.episodes, args.verbose)
