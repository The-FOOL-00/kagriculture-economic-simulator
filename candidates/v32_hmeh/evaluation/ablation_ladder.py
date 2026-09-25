# SPDX-License-Identifier: MIT
"""HMEH Causal Mechanism Ablation Ladder Runner.

Runs paired evaluations across development seeds (249675-249684) for:
- A7 Baseline
- HMEH-0: A7 opening + deterministic chore executor
- HMEH-1: HMEH-0 + Adaptive Labor
- HMEH-2: HMEH-1 + Shop-Conditioned Production
- HMEH-3: HMEH-2 + Market-Aware Selling
- HMEH-4: HMEH-3 + Terminal Liquidation
"""

from __future__ import annotations
import argparse
import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HMEH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, HMEH_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_hmeh.main import make_hmeh_agent

DEV_SEEDS = list(range(249675, 249685))  # 10 development seeds (249675-249684)


def _to_callable(agent):
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return lambda o, c=None: agent.act(o, c)
    elif callable(agent):
        return agent
    raise ValueError(f"Agent {agent} is not callable")


def _run_single_match(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    policy_name, opp_id, seed, seat = args
    check_seed_allowed(seed)
    
    # Instantiate agents
    if policy_name in ("A7", "E2_A7"):
        p_agent = load_agent("E9_AST")  # Standalone frozen A7
    elif policy_name == "V3":
        p_agent = load_agent("E0_V3")
    else:
        p_agent, _ = make_hmeh_agent(stage=policy_name)
        
    opp_agent = load_agent(opp_id)
    
    p_callable = _to_callable(p_agent)
    opp_callable = _to_callable(opp_agent)
    
    agents = [p_callable, opp_callable] if seat == 0 else [opp_callable, p_callable]
    
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    env.run(agents)
    duration = time.time() - t0
    
    final_step = env.steps[-1]
    p_reward = float(final_step[seat]["reward"] or 0.0)
    opp_reward = float(final_step[1 - seat]["reward"] or 0.0)
    delta = p_reward - opp_reward
    win = 1.0 if delta > 0 else (0.5 if delta == 0 else 0.0)
    
    # Step 0 check
    step0_mkt = env.steps[1][seat]["action"].get("market") or []
    
    # Final production stats from farm observation
    final_farm = final_step[seat]["observation"]["farms"][seat]
    tiles = final_farm.get("tiles", [])
    
    plants = 0
    animals = 0
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants += 1
                elif k == "PASTURE" and t.get("animal"):
                    animals += 1
                    
    hands_hired = len(final_farm.get("hands", []))
    
    return {
        "policy": policy_name,
        "opp": opp_id,
        "seed": seed,
        "seat": seat,
        "cash": p_reward,
        "opp_cash": opp_reward,
        "delta": delta,
        "win": win,
        "plants": plants,
        "animals": animals,
        "workers": 1 + hands_hired,
        "duration": duration,
        "step0_mkt": step0_mkt
    }


def run_ablation_stage(
    stage: str,
    opponent: str = "E0_V3",
    seeds: List[int] = None,
    max_workers: int = 4
) -> List[Dict[str, Any]]:
    assert_frozen()
    seeds = seeds or DEV_SEEDS
    tasks = []
    
    for s in seeds:
        for seat in (0, 1):
            tasks.append((stage, opponent, s, seat))
            
    print(f"\n=======================================================")
    print(f"RUNNING ABLATION: Policy={stage} vs {opponent} across {len(seeds)} seeds (2 seats)")
    print(f"=======================================================")
    
    results = []
    # If workers <= 1, run serially
    if max_workers <= 1:
        for t in tasks:
            res = _run_single_match(t)
            print(f"  Seed {res['seed']} Seat {res['seat']}: Cash=${res['cash']:,.2f} Opp=${res['opp_cash']:,.2f} Delta=${res['delta']:+,.2f} ({res['duration']:.1f}s)")
            results.append(res)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_run_single_match, t): t for t in tasks}
            for fut in as_completed(futures):
                res = fut.result()
                print(f"  Seed {res['seed']} Seat {res['seat']}: Cash=${res['cash']:,.2f} Opp=${res['opp_cash']:,.2f} Delta=${res['delta']:+,.2f} ({res['duration']:.1f}s)")
                results.append(res)
                
    # Compute summary statistics
    cash_vals = [r["cash"] for r in results]
    deltas = [r["delta"] for r in results]
    wins = [r["win"] for r in results]
    
    print("\n----------------- SUMMARY STATISTICS -----------------")
    print(f"Policy: {stage} vs {opponent}")
    print(f"Total Legs: {len(results)}")
    print(f"Mean Cash:   ${np.mean(cash_vals):,.2f}")
    print(f"Median Cash: ${np.median(cash_vals):,.2f}")
    print(f"P25 Cash:    ${np.percentile(cash_vals, 25):,.2f}")
    print(f"P75 Cash:    ${np.percentile(cash_vals, 75):,.2f}")
    print(f"Mean Delta:  ${np.mean(deltas):+,.2f}")
    print(f"Win Rate:    {np.mean(wins)*100:.1f}% ({sum(1 for w in wins if w == 1.0)}W / {sum(1 for w in wins if w == 0.0)}L / {sum(1 for w in wins if w == 0.5)}T)")
    print("------------------------------------------------------\n")
    
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stages", nargs="+", default=["A7", "HMEH-0"], help="Stages to run")
    parser.add_argument("--opp", default="E0_V3", help="Opponent ID")
    parser.add_argument("--seeds", type=int, nargs="+", default=None, help="Seeds to evaluate")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--out", default="candidates/v32_hmeh/reports/ablation_results.json", help="Output file")
    args = parser.parse_args()
    
    all_data = {}
    for st in args.stages:
        res = run_ablation_stage(st, opponent=args.opp, seeds=args.seeds, max_workers=args.workers)
        all_data[st] = res
        
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"Saved results to {args.out}")


if __name__ == "__main__":
    main()
