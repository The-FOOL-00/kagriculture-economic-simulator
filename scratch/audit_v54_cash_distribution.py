import statistics
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

def play_match(fn0, fn1, s):
    game = kagsim.Game(s)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)

idle = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}

# Test across 100 diverse seeds
seeds = [1000 + i * 17 for i in range(100)]

scores_idle = []
scores_self0 = []
scores_self1 = []

for s in seeds:
    # vs IDLE
    r0, _ = play_match(v54_plus_residual.agent, idle, s)
    scores_idle.append(r0)
    
    # Self play
    r_s0, r_s1 = play_match(v54_plus_residual.agent, v54_plus_residual.agent, s)
    scores_self0.append(r_s0)
    scores_self1.append(r_s1)

print("=" * 65)
print("V54++ RESIDUAL CASH DISTRIBUTION (100 SEEDS)")
print("=" * 65)

print("\n--- 1. SOLO VS IDLE ---")
print(f"Mean   : ${statistics.mean(scores_idle):,.2f}")
print(f"Median : ${statistics.median(scores_idle):,.2f}")
print(f"Min    : ${min(scores_idle):,.2f}")
print(f"Max    : ${max(scores_idle):,.2f}")
print(f"P90    : ${statistics.quantiles(scores_idle, n=10)[8]:,.2f}")
print(f"P99    : ${statistics.quantiles(scores_idle, n=100)[98]:,.2f}")

all_self = scores_self0 + scores_self1
print("\n--- 2. SELF-PLAY COMPETITIVE ---")
print(f"Mean   : ${statistics.mean(all_self):,.2f}")
print(f"Median : ${statistics.median(all_self):,.2f}")
print(f"Min    : ${min(all_self):,.2f}")
print(f"Max    : ${max(all_self):,.2f}")
print(f"P90    : ${statistics.quantiles(all_self, n=10)[8]:,.2f}")
print(f"P99    : ${statistics.quantiles(all_self, n=100)[98]:,.2f}")
print("=" * 65)
