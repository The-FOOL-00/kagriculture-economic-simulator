# SPDX-License-Identifier: MIT
"""
Prototype script to evaluate exact counterfactual reproduction with resynchronization metrics.
"""
import copy
import json
import time
from typing import Any, Dict, Tuple

import sys
import os
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

def run_counterfactual_with_resync(
    seed: int,
    opponent_id: str,
    seat: int,
    branch_step: int,
    candidate_macro_action: int,
    macro_duration: int = 4,
    resync_window: int = 24
):
    """
    Runs both pure A7 baseline and Candidate (A7 -> candidate for 4 ticks -> A7),
    recording exact state snapshots at:
      - branch_step (before intervention)
      - branch_step + macro_duration (immediate post-option)
      - branch_step + macro_duration + resync_window (post-resync)
      - 719 (terminal)
    """
    executor = StrategicExecutor()
    resync_step = min(719, branch_step + macro_duration + resync_window)
    post_opt_step = min(719, branch_step + macro_duration)

    # 1. Run Pure A7 Baseline
    env_a7 = make("kaggriculture", configuration={"seed": seed})
    env_a7.reset()
    a7_agent_base = load_agent("E9_AST")
    opp_base = load_league_opponent(opponent_id)

    snapshots_a7 = {}

    while not env_a7.done:
        p_obs = _get_shared_obs(env_a7, seat)
        opp_obs = _get_shared_obs(env_a7, 1 - seat)
        cur_step = int(p_obs.get("step", 0) or 0)

        if cur_step in (branch_step, post_opt_step, resync_step, 718):
            farm = p_obs.get("farms", [{}, {}])[seat]
            private = p_obs.get("private", {})
            snapshots_a7[cur_step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
                "shed": copy.deepcopy(private.get("shed", {})),
                "unlocked_quadrants": len(farm.get("unlocked_quadrants", [])),
            }

        act_p = a7_agent_base.act(p_obs)
        act_opp = opp_base(opp_obs)
        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    final_cash_a7 = float(env_a7.steps[-1][seat]["reward"] or 0.0)

    # 2. Run Candidate (A7 -> candidate H ticks -> A7)
    env_cand = make("kaggriculture", configuration={"seed": seed})
    env_cand.reset()
    a7_agent_cand = load_agent("E9_AST")
    opp_cand = load_league_opponent(opponent_id)

    snapshots_cand = {}

    while not env_cand.done:
        p_obs = _get_shared_obs(env_cand, seat)
        opp_obs = _get_shared_obs(env_cand, 1 - seat)
        cur_step = int(p_obs.get("step", 0) or 0)

        if cur_step in (branch_step, post_opt_step, resync_step, 718):
            farm = p_obs.get("farms", [{}, {}])[seat]
            private = p_obs.get("private", {})
            snapshots_cand[cur_step] = {
                "money": float(farm.get("money", 0.0) or 0.0),
                "farmer": copy.deepcopy(farm.get("farmer")),
                "hands": copy.deepcopy(farm.get("hands", [])),
                "shed": copy.deepcopy(private.get("shed", {})),
                "unlocked_quadrants": len(farm.get("unlocked_quadrants", [])),
            }

        base_a7_act = a7_agent_cand.act(p_obs)
        act_opp = opp_cand(opp_obs)

        if branch_step <= cur_step < branch_step + macro_duration and candidate_macro_action != 0:
            features = extract_economic_features(p_obs, player=seat)
            act_p = executor.execute(
                macro_action=candidate_macro_action,
                observation=p_obs,
                features=features,
                base_a7_action=base_a7_act
            )
        else:
            act_p = base_a7_act

        if seat == 0:
            env_cand.step([act_p, act_opp])
        else:
            env_cand.step([act_opp, act_p])

    final_cash_cand = float(env_cand.steps[-1][seat]["reward"] or 0.0)

    # Calculate Deltas
    local_cash_a7 = snapshots_a7.get(post_opt_step, {}).get("money", 0.0)
    local_cash_cand = snapshots_cand.get(post_opt_step, {}).get("money", 0.0)
    local_delta = local_cash_cand - local_cash_a7

    resync_cash_a7 = snapshots_a7.get(resync_step, {}).get("money", 0.0)
    resync_cash_cand = snapshots_cand.get(resync_step, {}).get("money", 0.0)
    resync_delta = resync_cash_cand - resync_cash_a7

    terminal_delta = final_cash_cand - final_cash_a7

    # Calculate Resync State at post_opt_step and resync_step
    def compute_sync(step_key):
        snap_a = snapshots_a7.get(step_key, {})
        snap_c = snapshots_cand.get(step_key, {})
        farmer_match = (snap_a.get("farmer") == snap_c.get("farmer"))
        hands_a = snap_a.get("hands", [])
        hands_c = snap_c.get("hands", [])
        hands_match = (hands_a == hands_c)
        worker_count_match = (len(hands_a) == len(hands_c))
        
        # Calculate Manhattan displacement of farmer and hands
        disp = 0
        if not farmer_match and snap_a.get("farmer") and snap_c.get("farmer"):
            disp += abs(snap_a["farmer"][0] - snap_c["farmer"][0]) + abs(snap_a["farmer"][1] - snap_c["farmer"][1])
        for ha, hc in zip(hands_a, hands_c):
            if ha != hc:
                disp += abs(ha[0] - hc[0]) + abs(ha[1] - hc[1])
        disp += abs(len(hands_a) - len(hands_c)) * 10
        
        if farmer_match and hands_match:
            status = "SYNCED"
        elif worker_count_match and disp <= 4:
            status = "PARTIALLY_SYNCED"
        elif worker_count_match and disp <= 12:
            status = "RECOVERING"
        else:
            status = "DESYNCED"
            
        return {
            "status": status,
            "displacement": disp,
            "farmer_match": farmer_match,
            "hands_match": hands_match,
            "worker_count_match": worker_count_match,
            "cand_workers": len(hands_c),
            "a7_workers": len(hands_a),
            "cand_quads": snap_c.get("unlocked_quadrants", 0),
            "a7_quads": snap_a.get("unlocked_quadrants", 0),
        }

    sync_at_post = compute_sync(post_opt_step)
    sync_at_resync = compute_sync(resync_step)

    return {
        "seed": seed,
        "step": branch_step,
        "opponent": opponent_id,
        "seat": seat,
        "candidate": candidate_macro_action,
        "a7_terminal_cash": final_cash_a7,
        "cand_terminal_cash": final_cash_cand,
        "local_delta": local_delta,
        "resync_delta": resync_delta,
        "terminal_delta": terminal_delta,
        "sync_post_option": sync_at_post,
        "sync_post_resync": sync_at_resync,
    }

if __name__ == "__main__":
    test_cases = [
        (249635, "E2_A7", 0, 288, 9),      # EXPAND_LAND (+11179)
        (249637, "E8_DMITRII", 0, 144, 3), # LIQUIDATE_SURPLUS (+3924)
        (249636, "E8_DMITRII", 0, 216, 1), # OPPORTUNISTIC_SELL (+3420)
    ]
    for seed, opp, seat, step, act in test_cases:
        t0 = time.time()
        res = run_counterfactual_with_resync(seed, opp, seat, step, act)
        elapsed = time.time() - t0
        print(f"Seed {seed} Step {step} Opp {opp} Act {act}:")
        print(f"  Local Delta (t+4): +${res['local_delta']:.2f}")
        print(f"  Resync Delta (t+28): +${res['resync_delta']:.2f}")
        print(f"  Terminal Delta (t=719): +${res['terminal_delta']:.2f}")
        print(f"  Sync @ t+4: {res['sync_post_option']['status']} (disp={res['sync_post_option']['displacement']}, farmer={res['sync_post_option']['farmer_match']}, hands={res['sync_post_option']['hands_match']})")
        print(f"  Sync @ t+28: {res['sync_post_resync']['status']} (disp={res['sync_post_resync']['displacement']}, farmer={res['sync_post_resync']['farmer_match']}, hands={res['sync_post_resync']['hands_match']})")
        print(f"  Elapsed: {elapsed:.2f}s\n")
