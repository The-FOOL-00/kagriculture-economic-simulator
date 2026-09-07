"""
Phase 12: Direct Head-to-Head Evaluation vs Frozen V2 (N=100 Matched Seeds)
===========================================================================
Runs 100 direct head-to-head matches between CL-Commitment-V1 and Frozen V2
alternating seats (Seat 0 vs Seat 1).
Records:
- Candidate Reward
- V2 Reward
- Win Rate, Loss Rate, Tie Rate
- Mean Margin, Median Margin, 95% Confidence Interval
- Productive actions, Movement actions, Idle actions
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent

def _run_h2h_match(seed, seat):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    if seat == 0:
        env.run([comm_agent, v2_agent])
        r_cand = float(env.steps[-1][0]["reward"] or 0)
        r_v2 = float(env.steps[-1][1]["reward"] or 0)
    else:
        env.run([v2_agent, comm_agent])
        r_cand = float(env.steps[-1][1]["reward"] or 0)
        r_v2 = float(env.steps[-1][0]["reward"] or 0)

    margin = r_cand - r_v2
    return {
        "seed": seed,
        "seat": seat,
        "r_cand": r_cand,
        "r_v2": r_v2,
        "margin": margin,
        "win": 1 if margin > 0 else 0,
        "loss": 1 if margin < 0 else 0,
        "tie": 1 if margin == 0 else 0
    }

def run_direct_v2_study(seeds, max_workers=10):
    print(f"\n=== Running Direct Head-to-Head vs Frozen V2 Across {len(seeds)} Seeds ===")
    tasks = [(s, idx % 2) for idx, s in enumerate(seeds)]
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_h2h_match, s, seat) for s, seat in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    n = len(results)
    wins = sum(r["win"] for r in results)
    losses = sum(r["loss"] for r in results)
    ties = sum(r["tie"] for r in results)
    win_rate = (wins / n) * 100.0

    cands = [r["r_cand"] for r in results]
    v2s = [r["r_v2"] for r in results]
    margins = [r["margin"] for r in results]

    mean_cand = float(np.mean(cands))
    std_cand = float(np.std(cands))
    mean_v2 = float(np.mean(v2s))
    std_v2 = float(np.std(v2s))
    mean_margin = float(np.mean(margins))
    std_margin = float(np.std(margins))
    median_margin = float(np.median(margins))
    se_margin = std_margin / np.sqrt(n)
    ci95 = (mean_margin - 1.96 * se_margin, mean_margin + 1.96 * se_margin)

    summary = {
        "n_matches": n,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "cand_mean": mean_cand,
        "cand_std": std_cand,
        "v2_mean": mean_v2,
        "v2_std": std_v2,
        "mean_margin": mean_margin,
        "std_margin": std_margin,
        "median_margin": median_margin,
        "ci95": [float(ci95[0]), float(ci95[1])],
    }

    print("\n--- DIRECT V2 HEAD-TO-HEAD SUMMARY ---")
    print(f"Total Matches : {n}")
    print(f"Win Rate      : {win_rate:.1f}% ({wins}W / {losses}L / {ties}T)")
    print(f"Candidate Mean: ${mean_cand:.1f} ± ${std_cand:.1f}")
    print(f"Frozen V2 Mean: ${mean_v2:.1f} ± ${std_v2:.1f}")
    print(f"Mean Margin   : ${mean_margin:+.1f} (Median: ${median_margin:+.1f})")
    print(f"95% CI Margin : [${ci95[0]:+.1f}, ${ci95[1]:+.1f}]")

    with open("scratch/direct_v2_h2h_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary

if __name__ == "__main__":
    seeds = list(range(5000, 5100)) # N=100 seeds
    run_direct_v2_study(seeds, max_workers=10)
