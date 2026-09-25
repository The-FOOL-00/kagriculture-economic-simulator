# SPDX-License-Identifier: MIT
"""
V32 P12 Experiment P12-01: Reproduce all 60 positive RL-X2 search targets
with exact local delta (t+4), post-resync delta (t+28), long-horizon terminal delta (t=719),
and physical resynchronization tracking.
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

ACTION_NAMES = {
    0: "FOLLOW_A7",
    1: "OPPORTUNISTIC_SELL",
    2: "SELECTIVE_PREEMPT_SELL",
    3: "LIQUIDATE_SURPLUS",
    4: "CROP_EXPANSION_MELON",
    5: "CROP_EXPANSION_WHEAT",
    6: "LIVESTOCK_EXPANSION_COW",
    7: "LIVESTOCK_EXPANSION_SHEEP",
    8: "PRESERVE_CASH",
    9: "EXPAND_LAND",
}

def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs

def evaluate_single_target(target_info: Dict[str, Any]) -> Dict[str, Any]:
    seed = target_info["seed"]
    opponent_id = target_info["opponent_id"]
    seat = target_info["seat"]
    branch_step = target_info["step"]
    candidate = target_info["best_action"]
    orig_best_delta = target_info.get("best_delta", 0.0)
    
    macro_duration = 4
    resync_window = 24
    post_opt_step = min(719, branch_step + macro_duration)
    resync_step = min(719, branch_step + macro_duration + resync_window)

    executor = StrategicExecutor()

    # 1. Baseline A7
    env_a7 = make("kaggriculture", configuration={"seed": seed})
    env_a7.reset()
    a7_agent = load_agent("E9_AST")
    opp_a7 = load_league_opponent(opponent_id)

    snap_a7 = {}
    while not env_a7.done:
        p_obs = _get_shared_obs(env_a7, seat)
        opp_obs = _get_shared_obs(env_a7, 1 - seat)
        step = int(p_obs.get("step", 0) or 0)

        if step in (branch_step, post_opt_step, resync_step):
            farm = p_obs.get("farms", [{}, {}])[seat]
            priv = p_obs.get("private", {})
            snap_a7[step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
                "shed": copy.deepcopy(priv.get("shed", {})),
                "quadrants": len(farm.get("unlocked_quadrants", [])),
            }

        act_p = a7_agent.act(p_obs)
        act_opp = opp_a7(opp_obs)
        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    final_cash_a7 = float(env_a7.steps[-1][seat]["reward"] or 0.0)

    # 2. Candidate (A7 -> candidate 4 ticks -> A7)
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
            priv = p_obs.get("private", {})
            snap_cand[step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
                "shed": copy.deepcopy(priv.get("shed", {})),
                "quadrants": len(farm.get("unlocked_quadrants", [])),
            }

        base_a7 = a7_cand.act(p_obs)
        act_opp = opp_cand(opp_obs)

        if branch_step <= step < branch_step + macro_duration and candidate != 0:
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

    # Resync analysis
    def get_disp(sa, sc):
        disp = 0
        fa = sa.get("farmer")
        fc = sc.get("farmer")
        if fa and fc and fa != fc:
            disp += abs(fa[0] - fc[0]) + abs(fa[1] - fc[1])
        ha = sa.get("hands", [])
        hc = sc.get("hands", [])
        disp += abs(len(ha) - len(hc)) * 10
        for p1, p2 in zip(ha, hc):
            if p1 != p2:
                disp += abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        farmer_ok = (fa == fc)
        hands_ok = (ha == hc)
        if farmer_ok and hands_ok:
            st = "SYNCED"
        elif len(ha) == len(hc) and disp <= 4:
            st = "PARTIALLY_SYNCED"
        elif len(ha) == len(hc) and disp <= 12:
            st = "RECOVERING"
        else:
            st = "DESYNCED"
        return st, disp, farmer_ok, hands_ok

    st_post, disp_post, f_ok_p, h_ok_p = get_disp(snap_a7.get(post_opt_step, {}), snap_cand.get(post_opt_step, {}))
    st_res, disp_res, f_ok_r, h_ok_r = get_disp(snap_a7.get(resync_step, {}), snap_cand.get(resync_step, {}))

    # Classify Mechanism and Repeatability Class (Section 9)
    # A. repeatable economic pattern
    # B. opponent-specific
    # C. seed-specific
    # D. one-step price accident
    # E. multi-step investment effect
    # F. production-chain effect
    # G. land effect
    # H. crop allocation effect
    # I. livestock effect
    # J. other
    mech_name = ACTION_NAMES.get(candidate, "UNKNOWN")
    if candidate == 9:
        rep_class = "G (land effect) + E (multi-step investment effect)"
    elif candidate in (4, 5):
        rep_class = "H (crop allocation effect) + E (multi-step investment effect)"
    elif candidate in (6, 7):
        rep_class = "I (livestock effect)"
    elif candidate in (1, 3):
        rep_class = "A (repeatable economic pattern) + D (price/liquidity timing)"
    elif candidate == 2:
        rep_class = "B (opponent-specific) + D (preemption)"
    elif candidate == 8:
        rep_class = "A (repeatable economic pattern) + E (capital preservation)"
    else:
        rep_class = "J (other)"

    return {
        "seed": seed,
        "step": branch_step,
        "opponent": opponent_id,
        "seat": seat,
        "candidate": candidate,
        "candidate_name": mech_name,
        "orig_delta": orig_best_delta,
        "a7_cash": final_cash_a7,
        "cand_cash": final_cash_cand,
        "local_delta": local_delta,
        "resync_delta": resync_delta,
        "terminal_delta": terminal_delta,
        "sync_post_opt": st_post,
        "disp_post_opt": disp_post,
        "sync_post_resync": st_res,
        "disp_post_resync": disp_res,
        "repeatability_class": rep_class,
        "reproduced": abs(terminal_delta - orig_best_delta) < 1.0,
    }

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    target_path = "candidates/v32_rlx2/reports/strategic_targets.jsonl"
    with open(target_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    pos_targets = [r for r in records if r.get("best_delta", 0) > 0]
    
    print(f"Launching reproduction of {len(pos_targets)} positive targets on 10 workers...")
    t0 = time.time()
    
    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(evaluate_single_target, t): t for t in pos_targets}
        completed = 0
        for fut in as_completed(future_map):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(pos_targets)}] Seed {res['seed']} Step {res['step']:3d} Opp {res['opponent'][:6]} "
                  f"Cand {res['candidate']} ({res['candidate_name'][:14]:14s}) -> "
                  f"TermDelta: +${res['terminal_delta']:8.2f} (Orig: +${res['orig_delta']:8.2f}) "
                  f"Sync: {res['sync_post_resync']} (reproduced: {res['reproduced']})",
                  flush=True)
                  
    elapsed = time.time() - t0
    print(f"\nAll {len(results)} targets evaluated in {elapsed:.2f}s!")
    
    # Sort by terminal delta descending
    results.sort(key=lambda x: x["terminal_delta"], reverse=True)
    
    # Save JSON results
    out_json = "candidates/v32_p12_options/reports/p12_01_reproduction.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON results to {out_json}")
    
    # Summary metrics
    reproduced_count = sum(1 for r in results if r["reproduced"])
    synced_post_count = sum(1 for r in results if r["sync_post_opt"] == "SYNCED")
    synced_resync_count = sum(1 for r in results if r["sync_post_resync"] == "SYNCED")
    
    print(f"\nSummary:")
    print(f"  Total positive targets: {len(results)}")
    print(f"  Exactly reproduced: {reproduced_count} / {len(results)} ({reproduced_count/len(results)*100:.1f}%)")
    print(f"  Physically SYNCED @ t+4: {synced_post_count} / {len(results)} ({synced_post_count/len(results)*100:.1f}%)")
    print(f"  Physically SYNCED @ t+28: {synced_resync_count} / {len(results)} ({synced_resync_count/len(results)*100:.1f}%)")
    
if __name__ == "__main__":
    main()
