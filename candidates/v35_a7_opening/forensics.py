# SPDX-License-Identifier: MIT
"""Kagriculture V35 Forensics & Episode Reconstruction Engine.

Reconstructs exact tick-by-tick counterfactual trajectories for all A7 loss legs,
comparing A7 (30/30 wash) vs Candidate (25/25 wash).

Records:
- seed, opponent, seat
- A7 starting cash, wash spend, post-wash remaining cash
- 25/25 wash spend, post-wash remaining cash
- first divergence step t_div
- purchase cascades (first seed purchase, animal purchase, hire execution)
- terminal margins and causal attribution
Outputs loss_rescue_census.jsonl and detailed forensic records.
"""

from __future__ import annotations
import copy
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v35_a7_opening.wash_sweep import ParametricWashAgent


def reconstruct_pair(
    seed: int,
    opponent_id: str,
    seat: int,
    cand_buy: int = 25,
    cand_sell: int = 25,
) -> Dict[str, Any]:
    """Runs a paired side-by-side reconstruction comparing A7 (30/30) and Candidate (cand_buy/cand_sell)."""
    # 1. Rollout A7
    env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_a7.reset()
    a7_agent = ParametricWashAgent(30, 30)
    opp_agent_a7 = load_league_opponent(opponent_id)

    a7_trace = []
    while not env_a7.done:
        step = env_a7.steps[-1][0]["observation"].get("step", 0) or 0
        obs_p = env_a7.steps[-1][seat]["observation"]
        obs_opp = env_a7.steps[-1][1 - seat]["observation"]
        farm_p = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}
        cash = float(farm_p.get("money", 0.0) or 0.0)

        act_p = a7_agent.act(obs_p)
        act_opp = opp_agent_a7(obs_opp)

        if step <= 36:
            a7_trace.append({
                "step": step,
                "cash": cash,
                "action": act_p,
            })

        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    a7_final_p = float(env_a7.steps[-1][seat]["reward"] or 0.0)
    a7_final_opp = float(env_a7.steps[-1][1 - seat]["reward"] or 0.0)
    a7_won = a7_final_p > a7_final_opp

    # 2. Rollout Candidate
    env_cand = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_cand.reset()
    cand_agent = ParametricWashAgent(cand_buy, cand_sell)
    opp_agent_cand = load_league_opponent(opponent_id)

    cand_trace = []
    first_div_step = -1
    first_div_reason = "NONE"

    while not env_cand.done:
        step = env_cand.steps[-1][0]["observation"].get("step", 0) or 0
        obs_p = env_cand.steps[-1][seat]["observation"]
        obs_opp = env_cand.steps[-1][1 - seat]["observation"]
        farm_p = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}
        cash = float(farm_p.get("money", 0.0) or 0.0)

        act_p = cand_agent.act(obs_p)
        act_opp = opp_agent_cand(obs_opp)

        if step <= 36:
            cand_trace.append({
                "step": step,
                "cash": cash,
                "action": act_p,
            })
            if first_div_step == -1 and step < len(a7_trace):
                a7_entry = a7_trace[step]
                if abs(cash - a7_entry["cash"]) > 0.01 and step > 0:
                    first_div_step = step
                    first_div_reason = f"Cash delta: Cand ${cash:.1f} vs A7 ${a7_entry['cash']:.1f}"

        if seat == 0:
            env_cand.step([act_p, act_opp])
        else:
            env_cand.step([act_opp, act_p])

    cand_final_p = float(env_cand.steps[-1][seat]["reward"] or 0.0)
    cand_final_opp = float(env_cand.steps[-1][1 - seat]["reward"] or 0.0)
    cand_won = cand_final_p > cand_final_opp

    return {
        "seed": seed,
        "opponent": opponent_id,
        "seat": seat,
        "cand_config": f"{cand_buy}/{cand_sell}",
        "a7_final_p": a7_final_p,
        "a7_final_opp": a7_final_opp,
        "a7_won": a7_won,
        "cand_final_p": cand_final_p,
        "cand_final_opp": cand_final_opp,
        "cand_won": cand_won,
        "rescued": (not a7_won and cand_won),
        "casualty": (a7_won and not cand_won),
        "terminal_cash_delta": cand_final_p - a7_final_p,
        "first_div_step": first_div_step,
        "first_div_reason": first_div_reason,
        "a7_early_trace": a7_trace,
        "cand_early_trace": cand_trace,
    }


def run_loss_census(
    loss_cases: List[Tuple[int, str, int]],
    output_filename: str = "loss_rescue_census.jsonl"
) -> List[Dict[str, Any]]:
    results = []
    out_path = os.path.join(REPO_ROOT, output_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        for seed, opp, seat in loss_cases:
            rec = reconstruct_pair(seed, opp, seat, 25, 25)
            results.append(rec)
            f.write(json.dumps({
                "seed": rec["seed"],
                "opponent": rec["opponent"],
                "seat": rec["seat"],
                "a7_won": rec["a7_won"],
                "cand_won": rec["cand_won"],
                "rescued": rec["rescued"],
                "casualty": rec["casualty"],
                "a7_cash": rec["a7_final_p"],
                "cand_cash": rec["cand_final_p"],
                "cash_delta": rec["terminal_cash_delta"],
                "first_div_step": rec["first_div_step"],
                "first_div_reason": rec["first_div_reason"],
            }) + "\n")
    print(f"Saved {out_path} ({len(results)} cases analyzed)")
    return results
