"""
=============================================================================
EVALUATE OPTIMIZED PREDICTIVE CHALLENGER (BATCH 8 + PREDICTIVE FRONTRUNNING)
=============================================================================
Tests if setting the base batch to 8 (less price slippage against town absorption)
combined with predictive frontrunning and emergency liquidity overrides beats
both Control V2 and Titan Production with >75% win rate.
=============================================================================
"""

import os
import sys
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from run_predictive_market_experiment import run_paired_benchmark, get_sha256, project_root

def main():
    control_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    challenger_path = os.path.join(project_root, "agents", "hybrid_predictive_market.py")
    titan_path = os.path.join(project_root, "opponents", "o1_titan.py")

    print("Evaluating Optimized Predictive Challenger (Batch 8 + Frontrunning)...")

    # 1. Challenger (Batch 8) vs Frozen Control V2 (100 matches)
    cfg_batch8 = {"base_batch": 8, "dynamic_batching": True, "enable_frontrunning": True}
    h2h_res = run_paired_benchmark(cfg_batch8, control_path, num_pairs=50, start_seed=60000, max_workers=6)
    print(f"\n1. Challenger (Batch 8) vs Control V2 [100 Matches]:")
    print(f"   Win Rate: {h2h_res['win_rate']:5.1f}% ({h2h_res['wins']}W - {h2h_res['losses']}L) | 95% CI: [{h2h_res['ci_95'][0]:4.1f}%, {h2h_res['ci_95'][1]:4.1f}%]")
    print(f"   Challenger Mean: ${h2h_res['mean_us']:8,.2f} | Control Mean: ${h2h_res['mean_opp']:8,.2f} | Net Margin: ${h2h_res['margin']:+8,.2f}")

    # 2. Challenger (Batch 8) vs Titan Production (60 matches)
    titan_res = run_paired_benchmark(cfg_batch8, titan_path, num_pairs=30, start_seed=61000, max_workers=6)
    print(f"\n2. Challenger (Batch 8) vs Titan Production [60 Matches]:")
    print(f"   Win Rate: {titan_res['win_rate']:5.1f}% ({titan_res['wins']}W - {titan_res['losses']}L) | 95% CI: [{titan_res['ci_95'][0]:4.1f}%, {titan_res['ci_95'][1]:4.1f}%]")
    print(f"   Challenger Mean: ${titan_res['mean_us']:8,.2f} | Titan Mean: ${titan_res['mean_opp']:8,.2f} | Net Margin: ${titan_res['margin']:+8,.2f}")

    out = {
        "h2h_vs_control": h2h_res,
        "vs_titan": titan_res
    }
    with open(os.path.join(project_root, "batch8_predictive_results.json"), "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
