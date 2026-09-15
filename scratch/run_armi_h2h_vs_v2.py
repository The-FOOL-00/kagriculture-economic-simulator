"""
Direct Head-to-Head Benchmark: ARM I (Synthesized) vs Frozen V2
Runs 100 matched games on Seeds 5000-5099 with alternating player seats (P0 vs P1).
Computes exact win rate, candidate mean cash, V2 mean cash, net margin, and 95% bootstrap CI.
"""

import sys
import os
import json
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from scratch.build_economic_arms import make_arm_i, make_arm_a

SEEDS = list(range(5000, 5100))

def _run_single_h2h_match(item):
    cand_factory, seed, cand_seat = item
    cand_agent = cand_factory()
    
    if cand_seat == 0:
        agents = [cand_agent, v2_agent]
    else:
        agents = [v2_agent, cand_agent]
        
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
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

def run_h2h_study(cand_factory, cand_name="ARM I (Synthesized)", max_workers=10):
    tasks = []
    for i, s in enumerate(SEEDS):
        cand_seat = i % 2
        tasks.append((cand_factory, s, cand_seat))
        
    print(f"\nRunning 100 Matched Head-to-Head Games: {cand_name} vs Frozen V2 (Seeds 5000-5099)...")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_h2h_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())
            
    elapsed = time.time() - t0
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
        "mean_net_margin": float(np.mean(margins)),
        "median_net_margin": float(np.median(margins)),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "elapsed_seconds": elapsed
    }
    
    print("=" * 80)
    print(f"DIRECT HEAD-TO-HEAD RESULTS: {cand_name} vs Frozen V2 (N = 100 Seeds)")
    print("=" * 80)
    print(f"Win Rate:            {report['win_rate']:5.1f}% ({wins}W / {losses}L / {ties}T)")
    print(f"Candidate Mean Cash: ${report['cand_mean_reward']:10,.2f} +/- ${report['cand_std_reward']:8,.2f} (Median: ${report['cand_median_reward']:10,.2f})")
    print(f"Frozen V2 Mean Cash: ${report['v2_mean_reward']:10,.2f} +/- ${report['v2_std_reward']:8,.2f} (Median: ${report['v2_median_reward']:10,.2f})")
    print(f"Mean Net Margin:     ${report['mean_net_margin']:10,.2f} [95% CI: ${report['ci_95_lower']:,.2f} to ${report['ci_95_upper']:,.2f}]")
    print(f"Median Net Margin:   ${report['median_net_margin']:10,.2f}")
    print(f"Benchmark Runtime:   {report['elapsed_seconds']:5.1f} seconds")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    report_i = run_h2h_study(make_arm_i, "ARM I (Synthesized)")
    with open("scratch/armi_h2h_vs_v2_results.json", "w") as f:
        json.dump(report_i, f, indent=2)
