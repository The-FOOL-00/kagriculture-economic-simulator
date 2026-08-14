"""
=============================================================================
LIVE LADDER SUBMISSION ANALYZER
=============================================================================
Utility to parse and monitor live Kaggle leaderboard episodes and performance.
=============================================================================
"""

import sys
import json
import os


def summarize_episodes(episode_dir="live_data/episodes"):
    if not os.path.exists(episode_dir):
        print(f"No episode directory found at {episode_dir}")
        return

    files = [f for f in os.listdir(episode_dir) if f.endswith(".json")]
    if not files:
        print("No live episode replays found in directory yet.")
        return

    print(f"Analyzing {len(files)} live episodes in {episode_dir}...")
    for f in files:
        path = os.path.join(episode_dir, f)
        try:
            with open(path, "r") as fp:
                data = json.load(fp)
            rewards = [step.get("reward") for step in data.get("steps", [])[-1]]
            print(f"Episode {f}: Final Rewards -> Us: {rewards[0]} | Opponent: {rewards[1]}")
        except Exception as e:
            print(f"Error reading {f}: {e}")


if __name__ == "__main__":
    ep_dir = sys.argv[1] if len(sys.argv) > 1 else "live_data/episodes"
    summarize_episodes(ep_dir)
