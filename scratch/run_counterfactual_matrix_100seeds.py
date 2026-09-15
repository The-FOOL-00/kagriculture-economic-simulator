import sys
import os
import json
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.counterfactual_policies_w1_w7 import (
    BaseQ50Agent,
    W1_SuppressPastureAgent,
    W2_SuppressClearingAgent,
    W3_SuppressAnimalPlacementAgent,
    W4_SuppressWheatHarvestAgent,
    W5_ProtectStrawberryHarvestAgent,
    W6_GatedLowerValueTasksAgent,
    W7_ShadowValueRankedAgent
)

AGENTS = {
    "M1_Baseline": m1_module.ClosedLoopEconomicV1,
    "Raw_Q50": BaseQ50Agent,
    "W1_SuppressPasture": W1_SuppressPastureAgent,
    "W2_SuppressClearing": W2_SuppressClearingAgent,
    "W3_SuppressAnimalPlacement": W3_SuppressAnimalPlacementAgent,
    "W4_SuppressWheatHarvest": W4_SuppressWheatHarvestAgent,
    "W5_ProtectStrawberryHarvest": W5_ProtectStrawberryHarvestAgent,
    "W6_GatedLowerValueTasks": W6_GatedLowerValueTasksAgent,
    "W7_ShadowRanked": W7_ShadowValueRankedAgent,
}

def run_agent_seed(args):
    agent_name, seed = args
    cls = AGENTS[agent_name]
    agent = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = float(steps[-1][0]["reward"])

    # Sold quantities
    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return {
        "agent": agent_name,
        "seed": seed,
        "reward": rew,
        "sold_qty": dict(sold_qty)
    }

def main():
    seeds = list(range(1250, 1350)) # 100 seeds
    print(f"Running W1-W7 Counterfactual Matrix across {len(seeds)} seeds (1250-1349)...")

    all_jobs = []
    for a_name in AGENTS.keys():
        for s in seeds:
            all_jobs.append((a_name, s))

    print(f"Total simulations: {len(all_jobs)} across {len(AGENTS)} agent variants...")

    results = defaultdict(dict)
    with ProcessPoolExecutor(max_workers=11) as executor:
        for res in executor.map(run_agent_seed, all_jobs, chunksize=5):
            results[res["agent"]][res["seed"]] = res

    # Summarize against Raw Q50 and M1 Baseline
    print("\n" + "="*115)
    print("PHASE 4: WORKER-TASK COUNTERFACTUAL MATRIX (SEEDS 1250-1349, N=100)")
    print("="*115)
    print(f"{'Variant':<28} | {'Mean Reward':<12} | {'Delta vs Q50':<14} | {'Win vs Q50':<11} | {'Delta vs M1':<14} | {'Win vs M1':<10} | {'Strawberry Sold':<15}")
    print("-" * 115)

    base_q50_rews = [results["Raw_Q50"][s]["reward"] for s in seeds]
    m1_rews = [results["M1_Baseline"][s]["reward"] for s in seeds]
    mean_q50 = np.mean(base_q50_rews)
    mean_m1 = np.mean(m1_rews)

    summary_data = []

    for a_name in AGENTS.keys():
        rews = [results[a_name][s]["reward"] for s in seeds]
        m_rew = np.mean(rews)
        del_q50 = m_rew - mean_q50
        del_m1 = m_rew - mean_m1

        win_q50 = sum(1 for s in seeds if results[a_name][s]["reward"] > results["Raw_Q50"][s]["reward"]) / len(seeds) * 100
        win_m1 = sum(1 for s in seeds if results[a_name][s]["reward"] > results["M1_Baseline"][s]["reward"]) / len(seeds) * 100

        sb_sold = np.mean([results[a_name][s]["sold_qty"].get("STRAWBERRY", 0) for s in seeds])

        print(f"{a_name:<28} | ${m_rew:>10,.2f} | {del_q50:>+12,.2f}  | {win_q50:>9.1f}%  | {del_m1:>+12,.2f}  | {win_m1:>8.1f}%  | {sb_sold:>12.2f} u")

        summary_data.append({
            "agent": a_name,
            "mean_reward": float(m_rew),
            "delta_vs_q50": float(del_q50),
            "win_rate_vs_q50": float(win_q50),
            "delta_vs_m1": float(del_m1),
            "win_rate_vs_m1": float(win_m1),
            "strawberry_sold": float(sb_sold)
        })

    with open("scratch/counterfactual_matrix_100seeds_results.json", "w") as f:
        json.dump({
            "summary": summary_data,
            "detailed": results
        }, f)
    print("\nSaved full results to scratch/counterfactual_matrix_100seeds_results.json")

if __name__ == "__main__":
    main()
