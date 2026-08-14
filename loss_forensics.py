"""
=============================================================================
LOSS FORENSICS & DIVERGENCE ANALYZER
=============================================================================
Automates large-scale benchmarking, captures every loss, and performs deep
comparative forensic analysis against Golden Control.
=============================================================================
"""

import os
import sys
import json
import numpy as np
from kaggle_environments import make
from concurrent.futures import ProcessPoolExecutor, as_completed


def analyze_loss_match(agent0_path, agent1_path, seed, swapped=False):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    if swapped:
        env.run([agent1_path, agent0_path])
        titan_idx = 1
        golden_idx = 0
    else:
        env.run([agent0_path, agent1_path])
        titan_idx = 0
        golden_idx = 1

    steps = env.steps
    final_step = steps[-1]
    
    titan_reward = float(final_step[titan_idx].reward or 0.0)
    golden_reward = float(final_step[golden_idx].reward or 0.0)
    
    if titan_reward >= golden_reward:
        # Not a loss
        return None

    loss_margin = golden_reward - titan_reward

    # Step-by-step divergence analysis
    first_diverge_step = None
    diverge_reason = "UNKNOWN"
    
    titan_cash_history = []
    golden_cash_history = []
    
    titan_crop_plants = {}
    golden_crop_plants = {}
    
    titan_sells = {}
    golden_sells = {}
    
    titan_unwatered_decays = 0
    golden_unwatered_decays = 0

    for step_idx, s in enumerate(steps):
        obs = s[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        
        t_farm = farms[titan_idx] if titan_idx < len(farms) else {}
        g_farm = farms[golden_idx] if golden_idx < len(farms) else {}
        
        t_money = t_farm.get("money", 0.0)
        g_money = g_farm.get("money", 0.0)
        
        titan_cash_history.append(t_money)
        golden_cash_history.append(g_money)
        
        # Track action divergence
        t_act = s[titan_idx].get("action", {}) or {}
        g_act = s[golden_idx].get("action", {}) or {}
        
        if first_diverge_step is None and str(t_act) != str(g_act):
            first_diverge_step = step_idx
            
        # Count sales
        for order in t_act.get("market", []):
            if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL":
                item = order[1]
                qty = int(order[2]) if len(order) >= 3 else 1
                titan_sells[item] = titan_sells.get(item, 0) + qty

        for order in g_act.get("market", []):
            if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL":
                item = order[1]
                qty = int(order[2]) if len(order) >= 3 else 1
                golden_sells[item] = golden_sells.get(item, 0) + qty

        # Count plants
        t_units = [t_act.get("farmer", [])] + t_act.get("hands", [])
        for u in t_units:
            if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT":
                crop = u[1]
                titan_crop_plants[crop] = titan_crop_plants.get(crop, 0) + 1

        g_units = [g_act.get("farmer", [])] + g_act.get("hands", [])
        for u in g_units:
            if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT":
                crop = u[1]
                golden_crop_plants[crop] = golden_crop_plants.get(crop, 0) + 1

    # Classify root cause
    # 1. Did Titan plant fewer high-value Melons early on?
    t_melons = titan_crop_plants.get("MELON", 0)
    g_melons = golden_crop_plants.get("MELON", 0)
    
    t_straw = titan_crop_plants.get("STRAWBERRY", 0)
    g_straw = golden_crop_plants.get("STRAWBERRY", 0)

    if g_melons > t_melons + 15:
        diverge_reason = "MELON_UNDERPLANTING"
    elif t_straw > g_straw + 10 and titan_reward < 32000:
        diverge_reason = "STRAWBERRY_OVEREXPOSURE"
    elif golden_sells.get("MELON", 0) > titan_sells.get("MELON", 0) + 20:
        diverge_reason = "MELON_HARVEST_SELLING_SLIPPAGE"
    elif first_diverge_step is not None and first_diverge_step < 24:
        diverge_reason = "DAY_0_PORTFOLIO_DIVERGENCE"
    else:
        diverge_reason = "LATE_GAME_LIQUIDATION_TIMING"

    return {
        "seed": seed,
        "swapped": swapped,
        "titan_reward": titan_reward,
        "golden_reward": golden_reward,
        "loss_margin": loss_margin,
        "first_diverge_step": first_diverge_step,
        "first_diverge_day": (first_diverge_step // 24) if first_diverge_step else None,
        "root_cause": diverge_reason,
        "titan_planted": titan_crop_plants,
        "golden_planted": golden_crop_plants,
        "titan_sold": titan_sells,
        "golden_sold": golden_sells,
    }


def run_forensic_suite(num_matches=100, start_seed=10000):
    print("=" * 75)
    print(f"RUNNING FORENSIC SUITE: main.py vs agents/golden_v1.py")
    print(f"Matches: {num_matches} | Start Seed: {start_seed} | Swap Sides: True")
    print("=" * 75)

    tasks = []
    for i in range(num_matches):
        seed = start_seed + i
        swapped = (i % 2 == 1)
        tasks.append(("main.py", "agents/golden_v1.py", seed, swapped))

    losses = []
    wins = 0
    ties = 0

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(analyze_loss_match, *t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            if res is not None:
                losses.append(res)
            else:
                wins += 1

    total = num_matches
    loss_count = len(losses)
    win_rate = wins / total * 100.0

    print("\n" + "=" * 75)
    print(f"FORENSIC BENCHMARK SUMMARY ({total} Matches)")
    print("=" * 75)
    print(f"Wins:   {wins:4d} ({win_rate:5.1f}%)")
    print(f"Losses: {loss_count:4d} ({loss_count/total*100:5.1f}%)")
    print("-" * 75)

    # Root cause clustering
    clusters = {}
    for l in losses:
        cause = l["root_cause"]
        clusters[cause] = clusters.get(cause, []) + [l]

    print("LOSS ROOT-CAUSE CLUSTERING (Pareto Breakdown):")
    for cause, items in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        avg_margin = np.mean([it["loss_margin"] for it in items])
        print(f"  • {cause:32s}: {len(items):2d} losses ({len(items)/loss_count*100:5.1f}%) | Avg Deficit: -${avg_margin:,.2f}")

    print("\nDETAILED LOSS LOG (First 10 Losses):")
    print(f"{'Seed':6s} | {'Titan Cash':12s} | {'Golden Cash':12s} | {'Deficit':10s} | {'Diverge Day':12s} | {'Root Cause'}")
    print("-" * 75)
    for l in sorted(losses, key=lambda x: x["loss_margin"], reverse=True)[:10]:
        print(f"{l['seed']:6d} | ${l['titan_reward']:10,.2f} | ${l['golden_reward']:10,.2f} | -${l['loss_margin']:8,.2f} | Day {l['first_diverge_day']:2d} (st {l['first_diverge_step']:3d}) | {l['root_cause']}")

    # Save to json for reference
    with open("forensic_losses.json", "w") as f:
        json.dump(losses, f, indent=2)

    print(f"\nSaved detailed forensic logs to forensic_losses.json")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    run_forensic_suite(num_matches=n, start_seed=s)
