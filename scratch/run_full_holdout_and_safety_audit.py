"""
scratch/run_full_holdout_and_safety_audit.py
=============================================================================
Phases 13, 14, 15, 16: Unseen Holdout Suite (400 Matches)
=============================================================================
Runs 400 unseen seeds across 5 major opponent matchups:
1. Frozen V2 vs Starter Baseline (80 matches, seat swapped)
2. Frozen V2 vs Aethel V1 (80 matches, seat swapped)
3. Frozen V2 vs Live Flooder (80 matches, seat swapped)
4. Frozen V2 vs Top Meta Replay (80 matches, seat swapped)
5. Guarded V2 vs Frozen V2 Head-to-Head (80 matches, seat swapped)

Computes:
- Mean scores & Margins
- Win / Loss / Tie counts & Win Rates
- 95% Confidence Intervals
- Median Margin & 5th Percentile
- Worst Losses
- Seat Symmetry
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

def run_single_match(args):
    seed, agent0_path, agent1_path, swapped = args
    cfg = {"seed": seed, "episodeSteps": 720}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    try:
        env.run([agent0_path, agent1_path])
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        
        if swapped:
            r0 = raw_r1
            r1 = raw_r0
        else:
            r0 = raw_r0
            r1 = raw_r1
            
        diff = r0 - r1
        win = 1 if diff > 0 else (0 if diff == 0 else -1)
        
        return {
            "seed": seed,
            "r0": r0,
            "r1": r1,
            "diff": diff,
            "win": win,
            "swapped": swapped
        }
    except Exception as e:
        print(f"Error seed {seed}: {e}")
        return {
            "seed": seed,
            "r0": 0.0,
            "r1": 0.0,
            "diff": 0.0,
            "win": -1,
            "swapped": swapped
        }

def run_holdout_audit(num_per_matchup=80, start_seed=6000, max_workers=6):
    print("=" * 80)
    print(f"STARTING UNSEEN HOLDOUT BENCHMARK (Seeds {start_seed} to {start_seed + num_per_matchup * 5})")
    print("=" * 80)
    
    matchup_configs = [
        ("V2 vs Starter", "candidates/slot2_aethel_refined_v2.py", None),
        ("V2 vs Aethel V1", "candidates/slot2_aethel_refined_v2.py", "agents/candidate_a_aethel_v1.py"),
        ("V2 vs Live Flooder", "candidates/slot2_aethel_refined_v2.py", "opponents/live_flooder_v1.py"),
        ("V2 vs Top Meta", "candidates/slot2_aethel_refined_v2.py", "opponents/o12_top_meta.py"),
        ("Guarded V2 vs Frozen V2", "scratch/v2_safety_overlay.py", "candidates/slot2_aethel_refined_v2.py"),
    ]
    
    all_summary = {}
    
    for idx, (title, a0_path, a1_path) in enumerate(matchup_configs):
        print(f"\n--- Benchmark: {title} ({num_per_matchup} matches, balanced seats) ---")
        tasks = []
        base_s = start_seed + idx * num_per_matchup
        for i in range(num_per_matchup):
            seed = base_s + i
            if i % 2 == 0:
                tasks.append((seed, a0_path, a1_path, False))
            else:
                tasks.append((seed, a1_path, a0_path, True))
                
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_single_match, t) for t in tasks]
            for f in as_completed(futures):
                results.append(f.result())
                
        scores_primary = [r["r0"] for r in results]
        scores_opp = [r["r1"] for r in results]
        margins = [r["diff"] for r in results]
        wins = sum(1 for r in results if r["win"] == 1)
        losses = sum(1 for r in results if r["win"] == -1)
        ties = sum(1 for r in results if r["win"] == 0)
        
        # Seat symmetry
        slot0_margins = [r["diff"] for r in results if not r["swapped"]]
        slot1_margins = [r["diff"] for r in results if r["swapped"]]
        
        mean_p = float(np.mean(scores_primary))
        mean_o = float(np.mean(scores_opp))
        mean_m = float(np.mean(margins))
        std_m = float(np.std(margins))
        median_m = float(np.median(margins))
        p5_m = float(np.percentile(margins, 5))
        worst_m = float(np.min(margins))
        win_rate = float(wins / len(results) * 100.0)
        ci95 = float(1.96 * (std_m / np.sqrt(len(margins))))
        
        print(f"Primary Mean Score:  ${mean_p:,.1f}")
        print(f"Opponent Mean Score: ${mean_o:,.1f}")
        print(f"Mean Margin:         ${mean_m:+,.1f} +/- ${ci95:,.1f}")
        print(f"Win Rate:            {win_rate:5.1f}% (W:{wins} L:{losses} T:{ties})")
        print(f"Median Margin:       ${median_m:+,.1f}")
        print(f"5th Percentile:      ${p5_m:+,.1f}")
        print(f"Worst Margin:        ${worst_m:+,.1f}")
        print(f"Seat 0 Mean Margin:  ${np.mean(slot0_margins):+,.1f}")
        print(f"Seat 1 Mean Margin:  ${np.mean(slot1_margins):+,.1f}")
        
        all_summary[title] = {
            "primary_mean_score": mean_p,
            "opp_mean_score": mean_o,
            "mean_margin": mean_m,
            "ci95": ci95,
            "win_rate_pct": win_rate,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "median_margin": median_m,
            "p5_margin": p5_m,
            "worst_margin": worst_m,
            "seat0_mean_margin": float(np.mean(slot0_margins)),
            "seat1_mean_margin": float(np.mean(slot1_margins)),
            "matches": len(results)
        }
        
    out_path = "scratch/holdout_audit_summary.json"
    with open(out_path, "w") as fp:
        json.dump(all_summary, fp, indent=2)
    print(f"\nSaved holdout summary to {out_path}")
    
    return all_summary

if __name__ == "__main__":
    run_holdout_audit(num_per_matchup=80, start_seed=6000, max_workers=6)
