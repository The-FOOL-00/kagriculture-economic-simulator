import os
import sys
import time
import json
import numpy as np
from kaggle_environments import make

# Ensure paths
sys.path.insert(0, os.path.abspath("."))

# Let's test running matches between V1, V2 and the archetypes
v1_path = "main.py"
v2_path = "candidates/slot2_aethel_refined_v2.py"

print("=" * 80)
print("TESTING LIVE-META HYPOTHESIS OFFLINE")
print("Evaluating V1 (Aethel-Prime) vs V2 (Aethel-Refined) against Live-Meta Archetypes")
print("=" * 80)

# Load existing opponent files from opponents/ directory
opponent_files = [
    ("o1_titan", "opponents/o1_titan.py"),
    ("o3_melon_specialist", "opponents/o3_melon_specialist.py"),
    ("o6_sheep_specialist", "opponents/o6_sheep_specialist.py"),
    ("o9_market_aggressor", "opponents/o9_market_aggressor.py"),
    ("o12_top_meta", "opponents/o12_top_meta.py")
]

# We will test 6 seeds per matchup for fast, highly informative results
seeds = [42, 100, 2026, 777, 999, 1234]

results = []

def run_match(agent0_path, agent1_path, seed, name0, name1):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    env.run([agent0_path, agent1_path])
    dur = time.time() - t0
    
    r0 = float(env.steps[-1][0].reward or 0)
    r1 = float(env.steps[-1][1].reward or 0)
    status0 = env.steps[-1][0].status
    status1 = env.steps[-1][1].status
    
    return {
        'seed': seed,
        'agent0': name0,
        'agent1': name1,
        'r0': r0,
        'r1': r1,
        'win0': 1 if r0 > r1 else (0.5 if r0 == r1 else 0),
        'margin0': r0 - r1,
        'duration': dur,
        'status0': status0,
        'status1': status1
    }

# 1. Direct Head-to-Head: V2 vs V1
print("\n--- 1. DIRECT HEAD-TO-HEAD: V2 vs V1 (6 seeds, symmetric 12 games) ---")
h2h_matches = []
for s in seeds:
    # V2 as P0, V1 as P1
    m1 = run_match(v2_path, v1_path, s, "V2", "V1")
    h2h_matches.append(m1)
    # Swapped: V1 as P0, V2 as P1
    m2 = run_match(v1_path, v2_path, s, "V1", "V2")
    # Swapped result from V2 perspective
    h2h_matches.append({
        'seed': s,
        'agent0': "V2",
        'agent1': "V1",
        'r0': m2['r1'],
        'r1': m2['r0'],
        'win0': 1 if m2['r1'] > m2['r0'] else (0.5 if m2['r1'] == m2['r0'] else 0),
        'margin0': m2['r1'] - m2['r0'],
        'duration': m2['duration'],
        'status0': m2['status1'],
        'status1': m2['status0']
    })

v2_h2h_wr = sum(m['win0'] for m in h2h_matches) / len(h2h_matches)
v2_h2h_margin = np.mean([m['margin0'] for m in h2h_matches])
v2_h2h_r0 = np.mean([m['r0'] for m in h2h_matches])
v2_h2h_r1 = np.mean([m['r1'] for m in h2h_matches])
print(f"V2 vs V1: Win Rate = {v2_h2h_wr*100:.1f}%, Mean V2 Reward = ${v2_h2h_r0:,.0f}, Mean V1 Reward = ${v2_h2h_r1:,.0f}, Margin = ${v2_h2h_margin:+,.0f}")

# 2. Benchmark Suite Comparison: V1 vs Opponents vs V2 vs Opponents
print("\n--- 2. BENCHMARK SUITE COMPARISON: V1 vs V2 across Archetypes ---")
comp_results = []
for opp_name, opp_path in opponent_files:
    if not os.path.exists(opp_path):
        continue
    # Run V1 vs Opp (symmetric)
    v1_wins, v1_rewards, v1_opp_rewards = [], [], []
    for s in seeds[:4]:
        m = run_match(v1_path, opp_path, s, "V1", opp_name)
        v1_wins.append(m['win0'])
        v1_rewards.append(m['r0'])
        v1_opp_rewards.append(m['r1'])
        
        m_swap = run_match(opp_path, v1_path, s, opp_name, "V1")
        v1_wins.append(1 if m_swap['r1'] > m_swap['r0'] else 0)
        v1_rewards.append(m_swap['r1'])
        v1_opp_rewards.append(m_swap['r0'])
        
    # Run V2 vs Opp (symmetric)
    v2_wins, v2_rewards, v2_opp_rewards = [], [], []
    for s in seeds[:4]:
        m = run_match(v2_path, opp_path, s, "V2", opp_name)
        v2_wins.append(m['win0'])
        v2_rewards.append(m['r0'])
        v2_opp_rewards.append(m['r1'])
        
        m_swap = run_match(opp_path, v2_path, s, opp_name, "V2")
        v2_wins.append(1 if m_swap['r1'] > m_swap['r0'] else 0)
        v2_rewards.append(m_swap['r1'])
        v2_opp_rewards.append(m_swap['r0'])
        
    v1_wr = np.mean(v1_wins) * 100
    v2_wr = np.mean(v2_wins) * 100
    v1_mean = np.mean(v1_rewards)
    v2_mean = np.mean(v2_rewards)
    
    comp_results.append({
        'Opponent': opp_name,
        'V1 WR': f"{v1_wr:.1f}%",
        'V1 Reward': f"${v1_mean:,.0f}",
        'V2 WR': f"{v2_wr:.1f}%",
        'V2 Reward': f"${v2_mean:,.0f}",
        'WR Diff': f"{v2_wr - v1_wr:+.1f}%",
        'Reward Diff': f"${v2_mean - v1_mean:+,.0f}"
    })

import pandas as pd
print(pd.DataFrame(comp_results).to_string(index=False))

with open("scratch/live_meta_experiment_results.json", "w", encoding="utf-8") as f:
    json.dump({
        'h2h': h2h_matches,
        'comparison': comp_results
    }, f, indent=2)
