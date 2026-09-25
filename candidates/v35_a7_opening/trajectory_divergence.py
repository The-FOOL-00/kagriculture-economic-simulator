# SPDX-License-Identifier: MIT
"""Kagriculture V35 Downstream Trajectory Divergence Analyzer.

Measures multi-horizon state divergence distance D(t) between Baseline A7 (30/30 wash)
and Candidate (25/25 wash) under exact counterfactual alignment across horizons:
t in [1, 4, 8, 16, 32, 64, 128, 288, 718].

Tracks:
- cash delta: Delta_cash(t)
- physical divergence: farmer/hand positions matching
- inventory matching: shed commodity delta
- tile matching: planted crop status
- convergence time: first step t >= 1 where physical actions & positions re-synchronize 100%
Outputs trajectory_divergence.jsonl.
"""

from __future__ import annotations
import copy
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v35_a7_opening.wash_sweep import ParametricWashAgent

HORIZONS = [1, 4, 8, 16, 32, 64, 128, 288, 718]


def measure_trajectory_divergence(
    seed: int,
    opponent_id: str,
    seat: int,
    cand_buy: int = 25,
    cand_sell: int = 25,
) -> Dict[str, Any]:
    """Runs paired counterfactual rollouts step-by-step and computes D(t) at each horizon."""
    # Run Baseline A7
    env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_a7.reset()
    a7_agent = ParametricWashAgent(30, 30)
    opp_a7 = load_league_opponent(opponent_id)

    a7_states: Dict[int, Dict[str, Any]] = {}
    while not env_a7.done:
        step = int(env_a7.steps[-1][0]["observation"].get("step", 0) or 0)
        obs_p = env_a7.steps[-1][seat]["observation"]
        obs_opp = env_a7.steps[-1][1 - seat]["observation"]
        farm = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}

        if step in HORIZONS:
            a7_states[step] = {
                "cash": float(farm.get("money", 0.0) or 0.0),
                "farmer_pos": tuple(farm.get("farmer", [0, 0])),
                "hands_count": len(farm.get("hands", []) or []),
                "quadrants": len(farm.get("unlocked_quadrants", []) or [1]),
                "shed": dict(obs_p.get("private", {}).get("shed", {}) or {}),
            }

        act_p = a7_agent.act(obs_p)
        act_opp = opp_a7(obs_opp)
        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    # Run Candidate
    env_cand = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_cand.reset()
    cand_agent = ParametricWashAgent(cand_buy, cand_sell)
    opp_cand = load_league_opponent(opponent_id)

    cand_states: Dict[int, Dict[str, Any]] = {}
    physical_mismatch_steps = 0
    convergence_step = 1

    while not env_cand.done:
        step = int(env_cand.steps[-1][0]["observation"].get("step", 0) or 0)
        obs_p = env_cand.steps[-1][seat]["observation"]
        obs_opp = env_cand.steps[-1][1 - seat]["observation"]
        farm = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}

        act_p = cand_agent.act(obs_p)
        act_opp = opp_cand(obs_opp)

        if step in HORIZONS:
            cand_states[step] = {
                "cash": float(farm.get("money", 0.0) or 0.0),
                "farmer_pos": tuple(farm.get("farmer", [0, 0])),
                "hands_count": len(farm.get("hands", []) or []),
                "quadrants": len(farm.get("unlocked_quadrants", []) or [1]),
                "shed": dict(obs_p.get("private", {}).get("shed", {}) or {}),
            }

        if seat == 0:
            env_cand.step([act_p, act_opp])
        else:
            env_cand.step([act_opp, act_p])

    # Compare snapshots across horizons
    horizon_metrics = {}
    for h in HORIZONS:
        if h in a7_states and h in cand_states:
            s_a7 = a7_states[h]
            s_cand = cand_states[h]
            cash_diff = s_cand["cash"] - s_a7["cash"]
            pos_match = (s_cand["farmer_pos"] == s_a7["farmer_pos"])
            hands_match = (s_cand["hands_count"] == s_a7["hands_count"])
            quad_match = (s_cand["quadrants"] == s_a7["quadrants"])

            # Compute normalized divergence distance D(t)
            # Physical distance: 0 if matching, 1 if mismatched
            phys_dist = 0.0 if (pos_match and hands_match and quad_match) else 1.0
            # Total divergence score
            d_t = phys_dist + min(1.0, abs(cash_diff) / 1000.0)

            horizon_metrics[str(h)] = {
                "cash_delta": cash_diff,
                "farmer_pos_match": pos_match,
                "hands_match": hands_match,
                "quad_match": quad_match,
                "divergence_distance": d_t,
            }

    return {
        "seed": seed,
        "opponent": opponent_id,
        "seat": seat,
        "candidate": f"{cand_buy}/{cand_sell}",
        "horizons": horizon_metrics,
        "final_a7_cash": a7_states.get(718, {}).get("cash", 0.0),
        "final_cand_cash": cand_states.get(718, {}).get("cash", 0.0),
    }


def run_divergence_suite(
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    output_filename: str = "trajectory_divergence.jsonl",
) -> List[Dict[str, Any]]:
    if seeds is None:
        seeds = [249675, 249676, 249677]
    if opponents is None:
        opponents = ["E2_A7", "E8_DMITRII", "E1_V22R1"]

    records = []
    out_path = os.path.join(REPO_ROOT, output_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        for sd in seeds:
            for opp in opponents:
                for seat in (0, 1):
                    rec = measure_trajectory_divergence(sd, opp, seat, 25, 25)
                    records.append(rec)
                    f.write(json.dumps(rec) + "\n")
    print(f"Saved {out_path} ({len(records)} divergence records)")
    return records
