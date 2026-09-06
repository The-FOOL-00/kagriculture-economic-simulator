"""
scratch/run_v2_safety_holdout_benchmark.py
=============================================================================
Phase 13, 14, 15, 16: Unseen Holdout Suite & Opponent Robustness (300+ Seeds)
=============================================================================
Runs 300+ fresh, unseen holdout seeds across opponents:
1. Guarded V2 vs Frozen V2 (Head-to-Head Paired Symmetry)
2. Guarded V2 vs Aethel V1
3. Guarded V2 vs Live Flooder
4. Guarded V2 vs Top Meta
5. Guarded V2 vs Starter

Reports:
- Mean Score & Paired Margins
- Win Rates
- 95% Confidence Intervals
- Median Margin & 5th Percentile
- Worst Loss / Catastrophic Loss Rates
- Seat Symmetry
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import time
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as aethel_v1
import scratch.v2_guarded_candidate as guarded_v2

def get_opponent(name):
    if name == "starter":
        return None
    elif name == "v2":
        return v2.agent
    elif name == "guarded_v2":
        return guarded_v2.agent
    elif name == "aethel_v1":
        return aethel_v1.agent
    elif name == "live_flooder":
        import opponents.live_flooder_v1 as lf
        return lf.agent
    elif name == "top_meta":
        import opponents.o12_top_meta as tm
        return tm.agent
    return None

def run_single_match(args):
    seed, agent0_name, agent1_name = args
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env.reset()
    
    a0_fn = get_opponent(agent0_name)
    a1_fn = get_opponent(agent1_name)
    
    # If using class instance
    if agent0_name == "guarded_v2":
        a0_fn = guarded_v2.GuardedV2Agent()
    if agent1_name == "guarded_v2":
        a1_fn = guarded_v2.GuardedV2Agent()
        
    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        
        act0 = a0_fn(obs0) if a0_fn else "random"
        act1 = a1_fn(obs1) if a1_fn else "random"
        
        env.step([act0, act1])
        
    final_step = env.steps[-1]
    r0 = float(final_step[0].reward or 0.0)
    r1 = float(final_step[1].reward or 0.0)
    
    return {
        "seed": seed,
        "agent0": agent0_name,
        "agent1": agent1_name,
        "r0": r0,
        "r1": r1,
        "diff": r0 - r1,
        "win0": 1 if r0 > r1 else (0 if r0 == r1 else -1)
    }

def run_holdout_suite(num_matches_per_matchup=80, start_seed=5000, max_workers=6):
    print("=" * 80)
    print(f"STARTING UNSEEN HOLDOUT BENCHMARK (Seeds {start_seed} to {start_seed + num_matches_per_matchup * 5})")
    print("=" * 80)
    
    matchups = [
        ("guarded_v2", "v2", "Head-to-Head (Guarded V2 vs Frozen V2)"),
        ("guarded_v2", "aethel_v1", "Guarded V2 vs Aethel V1"),
        ("guarded_v2", "live_flooder", "Guarded V2 vs Live Flooder"),
        ("guarded_v2", "top_meta", "Guarded V2 vs Top Meta Replay"),
        ("guarded_v2", "starter", "Guarded V2 vs Starter Baseline"),
    ]
    
    all_results = {}
    
    for idx, (a0, a1, title) in enumerate(matchups):
        print(f"\n--- Running Matchup: {title} ({num_matches_per_matchup} matches with seat swapping) ---")
        tasks = []
        base_s = start_seed + idx * num_matches_per_matchup
        for i in range(num_matches_per_matchup):
            seed = base_s + i
            if i % 2 == 0:
                tasks.append((seed, a0, a1))
            else:
                tasks.append((seed, a1, a0))
                
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_single_match, t) for t in tasks]
            for f in as_completed(futures):
                results.append(f.result())
                
        # Re-orient perspective to Guarded V2
        scores_guarded = []
        scores_opp = []
        margins = []
        wins = 0
        losses = 0
        ties = 0
        
        for r in results:
            if r["agent0"] == "guarded_v2":
                sg = r["r0"]
                so = r["r1"]
            else:
                sg = r["r1"]
                so = r["r0"]
            diff = sg - so
            scores_guarded.append(sg)
            scores_opp.append(so)
            margins.append(diff)
            if diff > 0:
                wins += 1
            elif diff < 0:
                losses += 1
            else:
                ties += 1
                
        mean_g = float(np.mean(scores_guarded))
        mean_o = float(np.mean(scores_opp))
        mean_m = float(np.mean(margins))
        std_m = float(np.std(margins))
        median_m = float(np.median(margins))
        p5_m = float(np.percentile(margins, 5))
        worst_m = float(np.min(margins))
        win_rate = float((wins / len(results)) * 100.0)
        
        ci95 = float(1.96 * (std_m / np.sqrt(len(margins))))
        
        print(f"Guarded V2 Mean Score: ${mean_g:,.1f}")
        print(f"Opponent Mean Score:   ${mean_o:,.1f}")
        print(f"Mean Margin:           ${mean_m:+,.1f} +/- ${ci95:,.1f}")
        print(f"Win Rate:              {win_rate:5.1f}% (W:{wins} L:{losses} T:{ties})")
        print(f"Median Margin:         ${median_m:+,.1f}")
        print(f"5th Percentile Margin: ${p5_m:+,.1f}")
        print(f"Worst Margin:          ${worst_m:+,.1f}")
        
        all_results[title] = {
            "mean_guarded_score": mean_g,
            "mean_opp_score": mean_o,
            "mean_margin": mean_m,
            "ci95": ci95,
            "win_rate_pct": win_rate,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "median_margin": median_m,
            "p5_margin": p5_m,
            "worst_margin": worst_m,
            "sample_size": len(results)
        }
        
    out_file = "scratch/holdout_benchmark_results.json"
    with open(out_file, "w") as fp:
        json.dump(all_results, fp, indent=2)
    print(f"\nSaved complete holdout benchmark to {out_file}")
    
    return all_results

if __name__ == "__main__":
    run_holdout_suite(num_matches_per_matchup=80, start_seed=5000, max_workers=6)
