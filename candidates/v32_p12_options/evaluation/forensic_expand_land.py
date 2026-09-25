# SPDX-License-Identifier: MIT
"""
Parallel forensic analysis of EXPAND_LAND (Action 9) across multiple development seeds
to determine the exact generalized economic conditions under which land expansion is profitable.
"""

import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v32_rlx2.search import StrategicSearchEngine
from candidates.v32_rlx2.state import extract_economic_features

def _get_shared_obs(env, pos):
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs

def eval_expand_land_seed(params):
    s = params["seed"]
    o = params["opponent_id"]
    engine = StrategicSearchEngine()

    # 1. Run up to step 288 to extract state
    env = make("kaggriculture", configuration={"seed": s})
    env.reset()
    a7 = load_agent("E9_AST")
    opp = load_league_opponent(o)
    
    while not env.done:
        p_obs = _get_shared_obs(env, 0)
        opp_obs = _get_shared_obs(env, 1)
        if int(p_obs.get("step", 0) or 0) >= 288:
            break
        act0 = a7.act(p_obs)
        act1 = opp(opp_obs)
        env.step([act0, act1])

    feat = extract_economic_features(p_obs, player=0)
    
    # 2. Evaluate counterfactual for Action 9 vs Action 0
    val_cand = engine.evaluate_counterfactual(seed=s, opponent_id=o, seat=0, branch_step=288, candidate_macro_action=9, macro_duration=4)
    val_a7 = engine.evaluate_counterfactual(seed=s, opponent_id=o, seat=0, branch_step=288, candidate_macro_action=0, macro_duration=4)
    delta = val_cand - val_a7

    return {
        "seed": s,
        "opponent": o,
        "a7_cash": val_a7,
        "cand_cash": val_cand,
        "delta": delta,
        "step_288_cash": feat.cash,
        "quads": feat.unlocked_quadrants,
        "runway": feat.wage_runway_days,
        "shops": feat.unlocked_shops
    }

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    seeds = [249635, 249636, 249637, 249675, 249676, 249677]
    opponents = ["E2_A7", "E8_DMITRII"]
    tasks = [{"seed": s, "opponent_id": o} for s in seeds for o in opponents]

    print(f"Running parallel EXPAND_LAND forensic on {len(tasks)} tasks on 10 workers...")
    t0 = time.time()

    print(f"{'Seed':<8} {'Opp':<10} {'A7 Cash':<10} {'Cand Cash':<10} {'Delta':<10} {'Step 288 Money':<15} {'Quads':<6} {'Runway':<8} {'Shops'}")
    print("-" * 90)

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(eval_expand_land_seed, t): t for t in tasks}
        for fut in as_completed(future_map):
            r = fut.result()
            results.append(r)
            shops_str = ",".join(r["shops"][:3])
            print(f"{r['seed']:<8} {r['opponent']:<10} ${r['a7_cash']:<9.0f} ${r['cand_cash']:<9.0f} {r['delta']:+9.0f} ${r['step_288_cash']:<14.1f} {r['quads']:<6} {r['runway']:<7.1f} {shops_str}",
                  flush=True)

    elapsed = time.time() - t0
    print(f"\nAll forensic runs finished in {elapsed:.2f}s!")

if __name__ == "__main__":
    main()
