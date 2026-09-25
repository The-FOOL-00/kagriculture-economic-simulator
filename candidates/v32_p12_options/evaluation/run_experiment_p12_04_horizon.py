# SPDX-License-Identifier: MIT
"""
V32 P12 Experiment P12-04: OPTION-HORIZON ABLATION
Evaluates horizons H in {2, 4, 6, 8} on canonical targets across key mechanisms
measuring local delta, post-resync delta, terminal delta, and physical desynchronization.
"""

import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v32_rlx2.executor import StrategicExecutor
from candidates.v32_rlx2.state import extract_economic_features

def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs

def evaluate_horizon_target(params: Dict[str, Any]) -> Dict[str, Any]:
    seed = params["seed"]
    opponent_id = params["opponent_id"]
    seat = params["seat"]
    branch_step = params["step"]
    candidate = params["candidate"]
    horizon = params["horizon"]
    resync_window = 24

    executor = StrategicExecutor()

    # 1. Baseline A7
    env_a7 = make("kaggriculture", configuration={"seed": seed})
    env_a7.reset()
    a7_agent = load_agent("E9_AST")
    opp_a7 = load_league_opponent(opponent_id)

    snap_a7 = {}
    post_opt_step = min(719, branch_step + horizon)
    resync_step = min(719, branch_step + horizon + resync_window)

    while not env_a7.done:
        p_obs = _get_shared_obs(env_a7, seat)
        opp_obs = _get_shared_obs(env_a7, 1 - seat)
        step = int(p_obs.get("step", 0) or 0)

        if step in (branch_step, post_opt_step, resync_step):
            farm = p_obs.get("farms", [{}, {}])[seat]
            snap_a7[step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
            }

        act_p = a7_agent.act(p_obs)
        act_opp = opp_a7(opp_obs)
        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    final_cash_a7 = float(env_a7.steps[-1][seat]["reward"] or 0.0)

    # 2. Candidate Match with Horizon H
    env_cand = make("kaggriculture", configuration={"seed": seed})
    env_cand.reset()
    a7_cand = load_agent("E9_AST")
    opp_cand = load_league_opponent(opponent_id)

    snap_cand = {}
    while not env_cand.done:
        p_obs = _get_shared_obs(env_cand, seat)
        opp_obs = _get_shared_obs(env_cand, 1 - seat)
        step = int(p_obs.get("step", 0) or 0)

        if step in (branch_step, post_opt_step, resync_step):
            farm = p_obs.get("farms", [{}, {}])[seat]
            snap_cand[step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
            }

        base_a7 = a7_cand.act(p_obs)
        act_opp = opp_cand(opp_obs)

        if branch_step <= step < branch_step + horizon and candidate != 0:
            features = extract_economic_features(p_obs, player=seat)
            act_p = executor.execute(
                macro_action=candidate,
                observation=p_obs,
                features=features,
                base_a7_action=base_a7
            )
        else:
            act_p = base_a7

        if seat == 0:
            env_cand.step([act_p, act_opp])
        else:
            env_cand.step([act_opp, act_p])

    final_cash_cand = float(env_cand.steps[-1][seat]["reward"] or 0.0)

    local_delta = snap_cand.get(post_opt_step, {}).get("money", 0.0) - snap_a7.get(post_opt_step, {}).get("money", 0.0)
    resync_delta = snap_cand.get(resync_step, {}).get("money", 0.0) - snap_a7.get(resync_step, {}).get("money", 0.0)
    terminal_delta = final_cash_cand - final_cash_a7

    ha_res = snap_a7.get(resync_step, {}).get("hands", [])
    hc_res = snap_cand.get(resync_step, {}).get("hands", [])
    fa_res = snap_a7.get(resync_step, {}).get("farmer")
    fc_res = snap_cand.get(resync_step, {}).get("farmer")

    is_synced = (ha_res == hc_res and fa_res == fc_res)

    return {
        "seed": seed,
        "step": branch_step,
        "opponent": opponent_id,
        "candidate": candidate,
        "horizon": horizon,
        "local_delta": local_delta,
        "resync_delta": resync_delta,
        "terminal_delta": terminal_delta,
        "is_synced": is_synced,
    }

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    test_targets = [
        {"seed": 249635, "step": 288, "opponent_id": "E2_A7", "seat": 0, "candidate": 9, "name": "EXPAND_LAND"},
        {"seed": 249637, "step": 144, "opponent_id": "E8_DMITRII", "seat": 0, "candidate": 3, "name": "LIQUIDATE_SURPLUS"},
        {"seed": 249636, "step": 216, "opponent_id": "E8_DMITRII", "seat": 0, "candidate": 1, "name": "OPPORTUNISTIC_SELL"},
        {"seed": 249636, "step": 72, "opponent_id": "E8_DMITRII", "seat": 0, "candidate": 4, "name": "CROP_MELON"},
    ]

    horizons = [2, 4, 6, 8]
    tasks = []
    for t in test_targets:
        for h in horizons:
            p = dict(t)
            p["horizon"] = h
            tasks.append(p)

    print(f"Launching Experiment P12-04 (Horizon Ablation) across {len(tasks)} runs...")
    t0 = time.time()

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(evaluate_horizon_target, p): p for p in tasks}
        completed = 0
        for fut in as_completed(future_map):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(tasks)}] Mech={res['candidate']} H={res['horizon']} -> "
                  f"LocalDelta={res['local_delta']:+8.1f} | TermDelta={res['terminal_delta']:+8.1f} | Synced={res['is_synced']}",
                  flush=True)

    elapsed = time.time() - t0
    print(f"\nP12-04 complete in {elapsed:.2f}s!")

    out_path = "candidates/v32_p12_options/reports/p12_04_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path}")

if __name__ == "__main__":
    main()
