"""
=============================================================================
HEAD-TO-HEAD INVESTIGATION: 8C/4S vs 6C/3S & MULTI-OPPONENT TOURNAMENT
=============================================================================
Rigorously evaluates:
1. 8C/4S High-Capacity vs 6C/3S Baseline
2. Both candidates vs Golden Control v1, Titan, Market Aggressor, and Specialists
3. Paired side-swapping, Wilson 95% CI, margin distributions, catastrophic losses.
=============================================================================
"""

import os
import sys
import time
import json
import numpy as np

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tournament_engine import run_paired_tournament
CAND_8C4S = os.path.join(project_root, "candidates", "slot5_hybrid_8c4s.py")
CAND_6C3S = os.path.join(project_root, "agents", "hybrid_6c3s_10m.py")
CAND_LOOKAHEAD = os.path.join(project_root, "candidates", "slot4_hybrid_lookahead.py")
CAND_DYNAMIC = os.path.join(project_root, "candidates", "slot3_hybrid_dynamic.py")
TITAN_PROD = os.path.join(project_root, "opponents", "o1_titan.py")
GOLDEN_V1 = os.path.join(project_root, "opponents", "o2_golden_v1.py")
O3_MELON = os.path.join(project_root, "opponents", "o3_melon_specialist.py")
O4_FAST = os.path.join(project_root, "opponents", "o4_fast_crop.py")
O5_COW = os.path.join(project_root, "opponents", "o5_cow_specialist.py")
O6_SHEEP = os.path.join(project_root, "opponents", "o6_sheep_specialist.py")
O7_BALANCED = os.path.join(project_root, "opponents", "o7_balanced_livestock.py")
O8_DYNAMIC = os.path.join(project_root, "opponents", "o8_economic_optimizer.py")
O9_AGGRESSOR = os.path.join(project_root, "opponents", "o9_market_aggressor.py")
O10_ANTI_MELON = os.path.join(project_root, "opponents", "o10_anti_melon.py")
O11_ANTI_LIVESTOCK = os.path.join(project_root, "opponents", "o11_anti_livestock.py")
O12_TOP_META = os.path.join(project_root, "opponents", "o12_top_meta.py")

def main():
    print("=" * 95)
    print("KAGGRICULTURE COMPETITIVE INVESTIGATION: 8C/4S vs 6C/3S HEAD-TO-HEAD TOURNAMENT")
    print("=" * 95)

    tournaments = [
        ("8C/4S vs Golden Control v1", CAND_8C4S, GOLDEN_V1, 20, 20000),
        ("6C/3S vs Golden Control v1", CAND_6C3S, GOLDEN_V1, 20, 20000),
        ("8C/4S vs 6C/3S Direct Peer", CAND_8C4S, CAND_6C3S, 20, 20000),
        ("8C/4S vs Titan Production", CAND_8C4S, TITAN_PROD, 20, 20000),
        ("8C/4S vs O9 Market Aggressor", CAND_8C4S, O9_AGGRESSOR, 15, 20000),
        ("8C/4S vs O3 Melon Specialist", CAND_8C4S, O3_MELON, 15, 20000),
        ("8C/4S vs O5 Cow Specialist", CAND_8C4S, O5_COW, 15, 20000),
        ("8C/4S vs O10 Anti-Melon", CAND_8C4S, O10_ANTI_MELON, 15, 20000),
        ("8C/4S vs O4 Fast Crop", CAND_8C4S, O4_FAST, 15, 20000),
        ("8C/4S vs O6 Sheep Specialist", CAND_8C4S, O6_SHEEP, 15, 20000),
        ("8C/4S vs O7 Balanced Livestock", CAND_8C4S, O7_BALANCED, 15, 20000),
    ]

    results_summary = []

    for name, agent_a, agent_b, pairs, start_seed in tournaments:
        t0 = time.time()
        print(f"\nExecuting Tournament: {name} ({pairs * 2} matches)...")
        res = run_paired_tournament(agent_a, agent_b, num_pairs=pairs, start_seed=start_seed, max_workers=6)
        elapsed = time.time() - t0

        results_summary.append({
            "name": name,
            "pairs": pairs,
            "total_matches": res["games"],
            "wins": res["wins"],
            "losses": res["losses"],
            "ties": res["ties"],
            "win_rate": res["win_rate"],
            "ci_95": res["ci_95"],
            "mean_us": res["mean_us"],
            "std_us": res["std_us"],
            "mean_opp": res["mean_opp"],
            "margin": res["margin"],
            "worst_drawdown": res["worst_drawdown"],
            "catastrophic_losses": res["catastrophic_losses"],
            "elapsed": elapsed
        })

        print(f"  --> Win Rate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L-{res['ties']}T) | 95% CI: [{res['ci_95'][0]:4.1f}%, {res['ci_95'][1]:4.1f}%]")
        print(f"  --> Mean Cash: ${res['mean_us']:8,.2f} (±${res['std_us']:6,.0f}) vs Opp: ${res['mean_opp']:8,.2f} | Net Margin: {res['margin']:+8,.2f}")
        print(f"  --> Worst Drawdown: ${res['worst_drawdown']:+8,.2f} | Catastrophic Losses (< -$10k): {res['catastrophic_losses']}")

    print("\n" + "=" * 95)
    print("TOURNAMENT SUMMARY TABLE")
    print("=" * 95)
    print(f"{'Tournament Name':32s} | {'Matches':7s} | {'Win Rate':9s} | {'95% CI':14s} | {'Our Cash':10s} | {'Opp Cash':10s} | {'Margin':10s}")
    print("-" * 95)
    for r in results_summary:
        print(f"{r['name']:32s} | {r['total_matches']:7d} | {r['win_rate']:8.1f}% | [{r['ci_95'][0]:4.1f}%, {r['ci_95'][1]:4.1f}%] | ${r['mean_us']:8,.0f} | ${r['mean_opp']:8,.0f} | {r['margin']:+9,.0f}")
    print("=" * 95)

    with open(os.path.join(project_root, "head_to_head_results.json"), "w") as f:
        json.dump(results_summary, f, indent=2)

if __name__ == "__main__":
    main()
