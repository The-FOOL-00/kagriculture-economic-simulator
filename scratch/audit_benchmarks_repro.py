"""
Forensic Verification of Benchmarks, Matches, and Ablations
(Parts 7, 8, 9, 10, 11, 12, 13)
"""

import os
import sys
import time
import json
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 1. Reproduce Part 7: $72k Claim across 30 seeds with side swapping
def test_hybrid_cash_distribution(num_seeds=20):
    print("\n" + "="*80)
    print(f"PART 7 — REPRODUCING $72,000 CLAIM ACROSS {num_seeds} SEEDS (WITH SIDE SWAPPING)")
    print("="*80)
    
    agent_path = "agents/hybrid_6c3s_10m.py"
    opponent_path = "starter"
    
    rewards_p0 = []
    rewards_p1 = []
    
    seeds = [10000 + i * 37 for i in range(num_seeds)]
    
    print(f"{'Seed':6} | {'Side':4} | {'Agent Reward':14} | {'Opp Reward':14} | {'Agent Cash':12}")
    print("-" * 65)
    
    for s in seeds:
        # Agent as P0
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([agent_path, opponent_path])
        r0 = env.steps[-1][0].reward
        r1 = env.steps[-1][1].reward
        rewards_p0.append(r0)
        print(f"{s:6d} | P0   | ${r0:12,.2f} | ${r1:12,.2f} | ${r0:10,.2f}")
        
        # Agent as P1
        env_swap = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env_swap.run([opponent_path, agent_path])
        r0_s = env_swap.steps[-1][0].reward
        r1_s = env_swap.steps[-1][1].reward
        rewards_p1.append(r1_s)
        print(f"{s:6d} | P1   | ${r1_s:12,.2f} | ${r0_s:12,.2f} | ${r1_s:10,.2f}")
        
    all_rewards = rewards_p0 + rewards_p1
    print("\n--- SUMMARY METRICS ---")
    print(f"Total Matches:    {len(all_rewards)}")
    print(f"Mean Reward:      ${np.mean(all_rewards):,.2f}")
    print(f"Median Reward:    ${np.median(all_rewards):,.2f}")
    print(f"Std Dev:          ${np.std(all_rewards):,.2f}")
    print(f"Min Reward:       ${np.min(all_rewards):,.2f}")
    print(f"Max Reward:       ${np.max(all_rewards):,.2f}")
    print(f"P0 Mean:          ${np.mean(rewards_p0):,.2f}")
    print(f"P1 Mean:          ${np.mean(rewards_p1):,.2f}")
    print(f"Win Rate:         {sum(1 for r in all_rewards if r > 4000) / len(all_rewards) * 100:.1f}%")

# 2. Reproduce Part 8: 17-3 Result vs Titan Control
def test_hybrid_vs_titan(num_matches=20):
    print("\n" + "="*80)
    print(f"PART 8 — REPRODUCING HYBRID VS TITAN MATCHUP ({num_matches} MATCHES)")
    print("="*80)
    
    hybrid_path = "agents/hybrid_6c3s_10m.py"
    titan_path = "candidates/slot1_titan_control.py"
    
    wins = 0
    losses = 0
    ties = 0
    
    seeds = [20000 + i * 19 for i in range(num_matches)]
    
    print(f"{'Match':5} | {'Seed':6} | {'Hybrid Side':11} | {'Hybrid Cash':13} | {'Titan Cash':13} | {'Winner':8} | {'Margin':12}")
    print("-" * 80)
    
    for i, s in enumerate(seeds):
        side = "P0" if i % 2 == 0 else "P1"
        if side == "P0":
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([hybrid_path, titan_path])
            h_cash = env.steps[-1][0].reward
            t_cash = env.steps[-1][1].reward
        else:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([titan_path, hybrid_path])
            t_cash = env.steps[-1][0].reward
            h_cash = env.steps[-1][1].reward
            
        margin = h_cash - t_cash
        if margin > 0:
            winner = "HYBRID"
            wins += 1
        elif margin < 0:
            winner = "TITAN"
            losses += 1
        else:
            winner = "TIE"
            ties += 1
            
        print(f"{i+1:5d} | {s:6d} | {side:11} | ${h_cash:11,.2f} | ${t_cash:11,.2f} | {winner:8} | ${margin:+10,.2f}")
        
    print("\n--- MATCHUP SUMMARY ---")
    print(f"Record (W-L-T): {wins}W - {losses}L - {ties}T (Win Rate: {wins/num_matches*100:.1f}%)")

# 3. Reproduce Part 9: 100% Results vs Control & Archetypes
def test_synthetic_suite():
    print("\n" + "="*80)
    print("PART 9 — VERIFYING 100% RESULTS AGAINST SYNTHETIC ARCHETYPES & CONTROLS")
    print("="*80)
    
    hybrid_path = "agents/hybrid_6c3s_10m.py"
    opponents = [
        ("Starter Bot", "starter"),
        ("Golden Control v1", "agents/golden_v1.py"),
        ("Strawberry Rush", "agents/synthetic/strawberry_rush.py"),
        ("Melon Burst", "agents/synthetic/melon_burst.py"),
        ("Crop Efficient", "agents/synthetic/crop_efficient.py"),
        ("Land Expansion", "agents/synthetic/land_expansion.py"),
        ("Balanced Hybrid", "agents/synthetic/balanced.py"),
    ]
    
    seeds = [30001, 30002, 30003, 30004, 30005]
    
    print(f"{'Opponent':20} | {'Matches':7} | {'Record':7} | {'Win %':7} | {'Mean Hybrid':13} | {'Mean Opp':13} | {'Mean Margin':13}")
    print("-" * 95)
    
    for opp_name, opp_path in opponents:
        w = 0
        l = 0
        h_cashes = []
        o_cashes = []
        
        for s in seeds:
            # P0
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([hybrid_path, opp_path])
            h0 = env.steps[-1][0].reward
            o0 = env.steps[-1][1].reward
            h_cashes.append(h0)
            o_cashes.append(o0)
            if h0 > o0: w += 1
            else: l += 1
            
            # P1
            env_s = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env_s.run([opp_path, hybrid_path])
            o1 = env_s.steps[-1][0].reward
            h1 = env_s.steps[-1][1].reward
            h_cashes.append(h1)
            o_cashes.append(o1)
            if h1 > o1: w += 1
            else: l += 1
            
        tot = w + l
        mean_h = np.mean(h_cashes)
        mean_o = np.mean(o_cashes)
        margin = mean_h - mean_o
        print(f"{opp_name:20} | {tot:7d} | {w}W-{l}L  | {w/tot*100:5.1f}% | ${mean_h:11,.2f} | ${mean_o:11,.2f} | ${margin:+11,.2f}")

# 4. Reproduce Part 11, 12, 13: Ablation Study
def test_ablations():
    print("\n" + "="*80)
    print("PART 11, 12, 13 — REPRODUCING ABLATION STUDY & TESTING CARE +42K CLAIM")
    print("="*80)
    
    ablation_files = [
        ("Full Champion (Hybrid 6C3S 10M)", "ablation_agents/ablation_full.py"),
        ("Minus Livestock (Pure Crop)", "ablation_agents/ablation_no_livestock.py"),
        ("Minus Melons (Carrot/Wheat only)", "ablation_agents/ablation_no_melon.py"),
        ("Minus Animal Care (Feed only)", "ablation_agents/ablation_no_care.py"),
        ("Minus Town Sync (Unscheduled sell)", "ablation_agents/ablation_no_sync.py"),
        ("Plus Crop Fertilizer (Fert on melon)", "ablation_agents/ablation_plus_fertilizer.py"),
    ]
    
    seeds = [40001, 40002, 40003, 40004, 40005, 40006]
    
    print(f"{'Ablation Variant':35} | {'Mean Cash':12} | {'Median Cash':12} | {'Delta vs Full':14}")
    print("-" * 80)
    
    full_mean = None
    
    for label, path in ablation_files:
        cashes = []
        for s in seeds:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([path, "starter"])
            cashes.append(env.steps[-1][0].reward)
            
        m = np.mean(cashes)
        med = np.median(cashes)
        if full_mean is None:
            full_mean = m
            delta_str = "$0.00 (REF)"
        else:
            delta = m - full_mean
            delta_str = f"${delta:+12,.2f}"
            
        print(f"{label:35} | ${m:10,.2f} | ${med:10,.2f} | {delta_str:14}")

if __name__ == "__main__":
    test_hybrid_cash_distribution(20)
    test_hybrid_vs_titan(20)
    test_synthetic_suite()
    test_ablations()
