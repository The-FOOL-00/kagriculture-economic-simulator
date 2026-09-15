import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

REPLAY_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "opponents", "top1_tetsuya", "replays", "episode-104060611-replay.json")

with open(REPLAY_PATH, "r") as f:
    replay_data = json.load(f)

seed = replay_data["info"]["seed"] # 1372926326
tetsuya_actions = [step[0]["action"] for step in replay_data["steps"]]

def make_tetsuya_replay_agent():
    step_counter = [0]
    def agent(obs, configuration=None):
        s = step_counter[0]
        step_counter[0] += 1
        if s < len(tetsuya_actions):
            return tetsuya_actions[s]
        return {"farmer": ["PASS"], "hands": [], "market": []}
    return agent

def play_match(fn0, fn1, s):
    game = kagsim.Game(s)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)

print("=" * 65)
print(f"EVALUATING TETSUYA REPLAY ACTIONS ON SEED {seed}")
print("=" * 65)

# 1. Tetsuya vs IDLE
idle = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}
r_tetsuya_idle, _ = play_match(make_tetsuya_replay_agent(), idle, seed)
print(f"Tetsuya vs IDLE: ${r_tetsuya_idle:,.2f}")

# Compare V54++ vs IDLE on this same seed
r_v54_idle, _ = play_match(v54_plus_residual.agent, idle, seed)
print(f"V54++ vs IDLE  : ${r_v54_idle:,.2f}")
print(f"Solo Gap       : {r_tetsuya_idle - r_v54_idle:+,.2f}")

# 2. Tetsuya vs V54++ (Seat 0 Tetsuya, Seat 1 V54++)
r_tetsuya, r_v54 = play_match(make_tetsuya_replay_agent(), v54_plus_residual.agent, seed)
print(f"\nHead-to-Head on Seed {seed}:")
print(f"Seat 0 (Tetsuya) : ${r_tetsuya:,.2f}")
print(f"Seat 1 (V54++)   : ${r_v54:,.2f}")
print(f"Net Margin       : {r_tetsuya - r_v54:+,.2f}")
print("=" * 65)
