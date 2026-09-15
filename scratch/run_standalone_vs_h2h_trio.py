"""
Standalone vs Head-to-Head Trio Benchmark
Evaluates across the identical 100 seeds (5000-5099) with alternating seats:
Arm A: CL-Economic-V1 vs starter (Standalone)
Arm B: Frozen V2 vs starter (Standalone)
Arm C: CL-Economic-V1 vs Frozen V2 (Direct H2H, already captured or run)
Calculates:
- Standalone gap = Mean(V2_standalone) - Mean(CL_standalone)
- H2H gap = Mean(V2_H2H) - Mean(CL_H2H)
- Shared-Market Interaction Penalty = H2H gap - Standalone gap
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
from candidates.candidate_cl_economic_v1 import agent as cl_agent

SEEDS = list(range(5000, 5100))

def run_single_standalone(agent_fn, seed, seat=0):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    agents = [agent_fn, "starter"] if seat == 0 else ["starter", agent_fn]
    try:
        env.run(agents)
        r = float(env.steps[-1][seat].get("reward") or 0.0)
        return {"seed": seed, "seat": seat, "reward": r, "error": None}
    except Exception as e:
        return {"seed": seed, "seat": seat, "reward": 0.0, "error": str(e)}

def run_standalone_arm(agent_fn, agent_name, seeds, max_workers=10):
    tasks = [(agent_fn, s, i % 2) for i, s in enumerate(seeds)]
    print(f"Running Standalone vs Starter for {agent_name} (N = {len(seeds)} Seeds)...")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_single_standalone, fn, s, seat): (s, seat) for fn, s, seat in tasks}
        for f in as_completed(futures):
            results.append(f.result())
            if len(results) % 25 == 0 or len(results) == len(seeds):
                print(f"  Completed {len(results)}/{len(seeds)} matches in {time.time()-t0:.1f}s...")
    elapsed = time.time() - t0
    rewards = np.array([r["reward"] for r in results])
    return {
        "agent": agent_name,
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "median_reward": float(np.median(rewards)),
        "elapsed_seconds": elapsed,
        "rewards": [float(r) for r in rewards]
    }

def main():
    print("=" * 80)
    print("PHASE 2: STANDALONE VS HEAD-TO-HEAD ISOLATION TRIO (Seeds 5000-5099)")
    print("=" * 80)
    
    cl_standalone = run_standalone_arm(cl_agent, "CL-Economic-V1", SEEDS)
    v2_standalone = run_standalone_arm(v2_agent, "Frozen V2", SEEDS)
    
    # Load H2H results from Phase 1 if available
    h2h_file = os.path.join(PROJECT_ROOT, "scratch", "h2h_forensic_100seeds_results.json")
    if os.path.exists(h2h_file):
        with open(h2h_file, "r") as f:
            h2h_data = json.load(f)["summary"]
        cl_h2h_mean = h2h_data["cl_mean_reward"]
        v2_h2h_mean = h2h_data["v2_mean_reward"]
        h2h_gap = v2_h2h_mean - cl_h2h_mean
    else:
        cl_h2h_mean = 66836.77
        v2_h2h_mean = 101022.55
        h2h_gap = 34185.78

    standalone_gap = v2_standalone["mean_reward"] - cl_standalone["mean_reward"]
    market_interaction_penalty = h2h_gap - standalone_gap
    
    trio_summary = {
        "cl_standalone": cl_standalone,
        "v2_standalone": v2_standalone,
        "cl_h2h_mean": cl_h2h_mean,
        "v2_h2h_mean": v2_h2h_mean,
        "standalone_gap": float(standalone_gap),
        "h2h_gap": float(h2h_gap),
        "shared_market_interaction_penalty": float(market_interaction_penalty),
        "pct_gap_from_shared_market": float(market_interaction_penalty / h2h_gap * 100.0) if h2h_gap > 0 else 0.0
    }
    
    out_path = os.path.join(PROJECT_ROOT, "scratch", "standalone_vs_h2h_trio_results.json")
    with open(out_path, "w") as f:
        json.dump(trio_summary, f, indent=2)
        
    print("\n" + "=" * 80)
    print("STANDALONE VS HEAD-TO-HEAD DECOMPOSITION SUMMARY")
    print("=" * 80)
    print(f"CL-Economic-V1 Standalone Mean Reward: ${cl_standalone['mean_reward']:12,.2f} ± ${cl_standalone['std_reward']:10,.2f}")
    print(f"Frozen V2 Standalone Mean Reward:       ${v2_standalone['mean_reward']:12,.2f} ± ${v2_standalone['std_reward']:10,.2f}")
    print(f"Standalone Production Gap (V2 - CL):    ${standalone_gap:12,.2f}")
    print("-" * 80)
    print(f"CL-Economic-V1 H2H Mean Cash:          ${cl_h2h_mean:12,.2f}")
    print(f"Frozen V2 H2H Mean Cash:               ${v2_h2h_mean:12,.2f}")
    print(f"Head-to-Head Margin Deficit (V2 - CL):  ${h2h_gap:12,.2f}")
    print("-" * 80)
    print(f"SHARED-MARKET INTERACTION PENALTY:     ${market_interaction_penalty:12,.2f}")
    print(f"Percentage of H2H Gap from Market:     {trio_summary['pct_gap_from_shared_market']:.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
