"""
Direct Frozen-V2 Head-to-Head Benchmark (N = 100 Seeds, Alternating Seats)
==========================================================================
Runs 100 matched games against Production Slot 2 (Frozen V2) on Seeds 5000-5099.
Alternates player seats (Seat 0 vs Seat 1).
Reports exact win rate, mean/median rewards, net margins, and 95% bootstrap CI.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_v1_agent
from scratch.build_coordinated_candidate import agent as coord_agent

def _run_single_h2h_match(item):
    cand_fn, seed, cand_seat = item
    if cand_seat == 0:
        agents = [cand_fn, v2_agent]
    else:
        agents = [v2_agent, cand_fn]
        
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    try:
        env.run(agents)
        steps = env.steps
        r0 = float(steps[-1][0].reward or 0.0)
        r1 = float(steps[-1][1].reward or 0.0)
        
        cand_reward = r0 if cand_seat == 0 else r1
        v2_reward = r1 if cand_seat == 0 else r0
        margin = cand_reward - v2_reward
        
        if cand_reward > v2_reward:
            winner = "CAND"
        elif v2_reward > cand_reward:
            winner = "V2"
        else:
            winner = "TIE"
            
        return {
            "seed": seed,
            "cand_seat": cand_seat,
            "cand_reward": cand_reward,
            "v2_reward": v2_reward,
            "margin": margin,
            "winner": winner,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed,
            "cand_seat": cand_seat,
            "cand_reward": 0.0,
            "v2_reward": 0.0,
            "margin": 0.0,
            "winner": "ERROR",
            "error": str(e)
        }

def run_h2h_benchmark(cand_fn, cand_name="Candidate", seeds=list(range(5000, 5100)), max_workers=12):
    tasks = []
    for i, s in enumerate(seeds):
        cand_seat = i % 2 # alternate seats
        tasks.append((cand_fn, s, cand_seat))
        
    results = []
    print(f"\nRunning 100 Matched Head-to-Head Games: {cand_name} vs Frozen V2 (Seeds {seeds[0]}..{seeds[-1]})...")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_h2h_match, t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            
    cand_rewards = np.array([r["cand_reward"] for r in results])
    v2_rewards = np.array([r["v2_reward"] for r in results])
    margins = np.array([r["margin"] for r in results])
    
    wins = sum(1 for r in results if r["winner"] == "CAND")
    losses = sum(1 for r in results if r["winner"] == "V2")
    ties = sum(1 for r in results if r["winner"] == "TIE")
    
    boot_means = [np.mean(np.random.choice(margins, size=len(margins), replace=True)) for _ in range(5000)]
    ci_lower, ci_upper = np.percentile(boot_means, [2.5, 97.5])
    
    report = {
        "candidate": cand_name,
        "matches": len(results),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / len(results) * 100.0,
        "cand_mean_reward": float(np.mean(cand_rewards)),
        "cand_std_reward": float(np.std(cand_rewards)),
        "cand_median_reward": float(np.median(cand_rewards)),
        "v2_mean_reward": float(np.mean(v2_rewards)),
        "v2_std_reward": float(np.std(v2_rewards)),
        "v2_median_reward": float(np.median(v2_rewards)),
        "mean_margin": float(np.mean(margins)),
        "median_margin": float(np.median(margins)),
        "std_margin": float(np.std(margins)),
        "ci_95": [float(ci_lower), float(ci_upper)],
    }
    
    print("\n" + "=" * 75)
    print(f"DIRECT HEAD-TO-HEAD RESULTS: {cand_name} vs Frozen V2")
    print("=" * 75)
    print(f"Total Matches:    {len(results)} (50 Seat 0 / 50 Seat 1)")
    print(f"Win / Loss / Tie: {wins}W / {losses}L / {ties}T (Win Rate: {report['win_rate']:.1f}%)")
    print(f"Candidate Cash:   ${report['cand_mean_reward']:10.2f} ± ${report['cand_std_reward']:8.2f} (Median: ${report['cand_median_reward']:10.2f})")
    print(f"Frozen V2 Cash:   ${report['v2_mean_reward']:10.2f} ± ${report['v2_std_reward']:8.2f} (Median: ${report['v2_median_reward']:10.2f})")
    print(f"Net Margin:       ${report['mean_margin']:+10.2f} ± ${report['std_margin']:8.2f} (Median: ${report['median_margin']:+10.2f})")
    print(f"95% Bootstrap CI: [${ci_lower:+.2f}, ${ci_upper:+.2f}]")
    print("=" * 75)
    
    return report

if __name__ == "__main__":
    seeds = list(range(5000, 5100))
    print("Executing Comparative Head-to-Head Suite...")
    cl_v1_h2h = run_h2h_benchmark(comm_v1_agent, "CL-Commitment-V1 Baseline", seeds=seeds)
    coord_h2h = run_h2h_benchmark(coord_agent, "CL-Coordinated-V1", seeds=seeds)
    
    with open("scratch/direct_v2_head_to_head_comparative.json", "w") as f:
        json.dump({"commitment_v1": cl_v1_h2h, "coordinated_v1": coord_h2h}, f, indent=2)
