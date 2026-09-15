import sys
import os
import json
import numpy as np
from collections import defaultdict
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.conditional_policy_agents import PolicyC1Agent, PolicyC5Agent

def run_agent_metrics(agent, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    
    rew = float(steps[-1][0]["reward"])
    sold = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold[o[1]] += int(o[2])
                
    worker_moves = 0
    worker_idles = 0
    for st in steps:
        act = st[0].get("action") or {}
        f_act = act.get("farmer", ["PASS"])[0]
        if f_act in ("NORTH", "SOUTH", "EAST", "WEST"):
            worker_moves += 1
        elif f_act == "PASS":
            worker_idles += 1
        for h_act in act.get("hands", []):
            op = h_act[0] if h_act else "PASS"
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                worker_moves += 1
            elif op == "PASS":
                worker_idles += 1

    last_f0 = steps[-1][0]["observation"]["farms"][0]
    last_tiles = last_f0["tiles"]
    cows_final = sum(1 for r in last_tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    sheep_final = sum(1 for r in last_tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")

    return {
        "reward": rew,
        "sold": dict(sold),
        "worker_moves": worker_moves,
        "worker_idles": worker_idles,
        "cows": cows_final,
        "sheep": sheep_final
    }

def run_holdout_seed(seed):
    m1 = run_agent_metrics(m1_module.ClosedLoopEconomicV1(), seed)
    q50 = run_agent_metrics(ParameterizedQuotaAgent(50), seed)
    c1 = run_agent_metrics(PolicyC1Agent(50), seed)
    c5 = run_agent_metrics(PolicyC5Agent(50), seed)
    
    return {
        "seed": seed,
        "m1": m1,
        "q50": q50,
        "c1": c1,
        "c5": c5
    }

def main():
    seeds = list(range(1450, 1650)) # 200 fresh holdout seeds
    print(f"Executing FRESH HOLDOUT on untouched seeds 1450-1649 (N={len(seeds)})...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_holdout_seed, seeds))

    with open("scratch/fresh_holdout_1450_1649_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Finished Fresh Holdout evaluation. Saved to scratch/fresh_holdout_1450_1649_results.json.", flush=True)

if __name__ == "__main__":
    main()
