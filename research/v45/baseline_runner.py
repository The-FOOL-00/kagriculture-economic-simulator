# SPDX-License-Identifier: MIT
"""V45 Baseline Lock & V44 Reproduction Runner.

Executes a 128-leg paired benchmark (16 seeds x 4 opponents x 2 seats)
comparing V44 against the incumbent V35 baseline to verify exact reproducibility,
zero casualties, and lock the governance baseline.
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v45.governance import assert_protected_artifacts, assert_seed_safe
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

# 16 clean non-holdout seeds
BASELINE_SEEDS = [
    249635, 249636, 249637, 249638,
    249645, 249646, 249647, 249648,
    249655, 249656, 249657, 249658,
    249685, 249686, 249687, 249688
]

OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]


def _act(agent: Any, obs: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return agent.act(obs)
    return agent(obs)


def run_baseline_benchmark() -> Dict[str, Any]:
    print("=" * 80)
    print("V45 PHASE 0: GOVERNANCE VERIFICATION & BASELINE REPRODUCTION")
    print("=" * 80)
    
    # 1. Assert protected hashes
    hashes = assert_protected_artifacts()
    print("SUCCESS: Governance hashes verified.")
    
    # 2. Check holdout safety
    for s in BASELINE_SEEDS:
        assert_seed_safe(s)
    print(f"SUCCESS: All {len(BASELINE_SEEDS)} baseline seeds verified non-holdout.")
    
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}
    
    legs_data = []
    t0 = time.perf_counter()
    
    total_matchups = len(BASELINE_SEEDS) * len(OPPONENTS)
    print(f"Beginning 128-leg paired evaluation across {total_matchups} matchups...")
    
    match_idx = 0
    for seed in BASELINE_SEEDS:
        for opp_id in OPPONENTS:
            match_idx += 1
            opp_master = opp_masters[opp_id]
            
            # --- Seat 0: V44 as Player 0, Opponent as Player 1 ---
            sim_v44_0 = FastKagricultureSim(seed=seed)
            cand0 = V44CandidateController()
            opp0 = copy.deepcopy(opp_master)
            oc0, oc1 = sim_v44_0.reset(seed=seed)
            while not sim_v44_0.done:
                [oc0, oc1], _, _, _ = sim_v44_0.step([_act(cand0, oc0), opp0(oc1)])
            v44_cash_s0 = float(oc0["farms"][0]["money"])
            opp_cash_s0 = float(oc1["farms"][1]["money"])
            v44_win_s0 = v44_cash_s0 > opp_cash_s0
            v44_tie_s0 = v44_cash_s0 == opp_cash_s0
            v44_loss_s0 = v44_cash_s0 < opp_cash_s0
            v44_margin_s0 = v44_cash_s0 - opp_cash_s0
            
            # Baseline V35 in Seat 0
            sim_v35_0 = FastKagricultureSim(seed=seed)
            base0 = V35OpeningController()
            opp0_b = copy.deepcopy(opp_master)
            ob0, ob1 = sim_v35_0.reset(seed=seed)
            while not sim_v35_0.done:
                [ob0, ob1], _, _, _ = sim_v35_0.step([_act(base0, ob0), opp0_b(ob1)])
            v35_cash_s0 = float(ob0["farms"][0]["money"])
            v35_opp_cash_s0 = float(ob1["farms"][1]["money"])
            v35_win_s0 = v35_cash_s0 > v35_opp_cash_s0
            v35_tie_s0 = v35_cash_s0 == v35_opp_cash_s0
            v35_loss_s0 = v35_cash_s0 < v35_opp_cash_s0
            v35_margin_s0 = v35_cash_s0 - v35_opp_cash_s0

            # --- Seat 1: Opponent as Player 0, V44 as Player 1 ---
            sim_v44_1 = FastKagricultureSim(seed=seed)
            cand1 = V44CandidateController()
            opp1 = copy.deepcopy(opp_master)
            oc0, oc1 = sim_v44_1.reset(seed=seed)
            while not sim_v44_1.done:
                [oc0, oc1], _, _, _ = sim_v44_1.step([opp1(oc0), _act(cand1, oc1)])
            v44_cash_s1 = float(oc1["farms"][1]["money"])
            opp_cash_s1 = float(oc0["farms"][0]["money"])
            v44_win_s1 = v44_cash_s1 > opp_cash_s1
            v44_tie_s1 = v44_cash_s1 == opp_cash_s1
            v44_loss_s1 = v44_cash_s1 < opp_cash_s1
            v44_margin_s1 = v44_cash_s1 - opp_cash_s1

            # Baseline V35 in Seat 1
            sim_v35_1 = FastKagricultureSim(seed=seed)
            base1 = V35OpeningController()
            opp1_b = copy.deepcopy(opp_master)
            ob0, ob1 = sim_v35_1.reset(seed=seed)
            while not sim_v35_1.done:
                [ob0, ob1], _, _, _ = sim_v35_1.step([opp1_b(ob0), _act(base1, ob1)])
            v35_cash_s1 = float(ob1["farms"][1]["money"])
            v35_opp_cash_s1 = float(ob0["farms"][0]["money"])
            v35_win_s1 = v35_cash_s1 > v35_opp_cash_s1
            v35_tie_s1 = v35_cash_s1 == v35_opp_cash_s1
            v35_loss_s1 = v35_cash_s1 < v35_opp_cash_s1
            v35_margin_s1 = v35_cash_s1 - v35_opp_cash_s1

            # Leg 0
            leg0 = {
                "seed": seed, "opp_id": opp_id, "seat": 0,
                "v44_cash": v44_cash_s0, "opp_cash": opp_cash_s0,
                "v44_margin": v44_margin_s0, "v44_win": v44_win_s0, "v44_tie": v44_tie_s0, "v44_loss": v44_loss_s0,
                "v35_cash": v35_cash_s0, "v35_margin": v35_margin_s0, "v35_win": v35_win_s0, "v35_tie": v35_tie_s0, "v35_loss": v35_loss_s0,
                "cash_delta": v44_cash_s0 - v35_cash_s0,
                "margin_delta": v44_margin_s0 - v35_margin_s0,
                "rescue": int(not v35_win_s0 and v44_win_s0),
                "casualty": int(v35_win_s0 and not v44_win_s0),
            }
            # Leg 1
            leg1 = {
                "seed": seed, "opp_id": opp_id, "seat": 1,
                "v44_cash": v44_cash_s1, "opp_cash": opp_cash_s1,
                "v44_margin": v44_margin_s1, "v44_win": v44_win_s1, "v44_tie": v44_tie_s1, "v44_loss": v44_loss_s1,
                "v35_cash": v35_cash_s1, "v35_margin": v35_margin_s1, "v35_win": v35_win_s1, "v35_tie": v35_tie_s1, "v35_loss": v35_loss_s1,
                "cash_delta": v44_cash_s1 - v35_cash_s1,
                "margin_delta": v44_margin_s1 - v35_margin_s1,
                "rescue": int(not v35_win_s1 and v44_win_s1),
                "casualty": int(v35_win_s1 and not v44_win_s1),
            }
            legs_data.extend([leg0, leg1])
            
            if match_idx % 16 == 0 or match_idx == total_matchups:
                print(f"  Completed {match_idx}/{total_matchups} matchups ({len(legs_data)}/128 legs)...")

    dur = time.perf_counter() - t0
    print(f"All 128 legs executed in {dur:.1f}s.")
    
    # Aggregated metrics
    v44_wins = sum(1 for l in legs_data if l["v44_win"])
    v44_ties = sum(1 for l in legs_data if l["v44_tie"])
    v44_losses = sum(1 for l in legs_data if l["v44_loss"])
    v35_wins = sum(1 for l in legs_data if l["v35_win"])
    v35_ties = sum(1 for l in legs_data if l["v35_tie"])
    v35_losses = sum(1 for l in legs_data if l["v35_loss"])
    
    cash_deltas = [l["cash_delta"] for l in legs_data]
    margin_deltas = [l["margin_delta"] for l in legs_data]
    rescues = sum(l["rescue"] for l in legs_data)
    casualties = sum(l["casualty"] for l in legs_data)
    
    summary = {
        "total_legs": len(legs_data),
        "v44_record": {"wins": v44_wins, "ties": v44_ties, "losses": v44_losses, "win_rate": round(v44_wins / len(legs_data) * 100, 2)},
        "v35_record": {"wins": v35_wins, "ties": v35_ties, "losses": v35_losses, "win_rate": round(v35_wins / len(legs_data) * 100, 2)},
        "mean_cash_delta_vs_v35": round(float(np.mean(cash_deltas)), 2),
        "median_cash_delta_vs_v35": round(float(np.median(cash_deltas)), 2),
        "std_cash_delta_vs_v35": round(float(np.std(cash_deltas)), 2),
        "mean_margin_delta_vs_v35": round(float(np.mean(margin_deltas)), 2),
        "rescues": rescues,
        "casualties": casualties,
        "opponents": OPPONENTS,
        "seeds": BASELINE_SEEDS,
        "hashes": hashes,
    }
    
    os.makedirs(os.path.join(REPO_ROOT, "research", "v45", "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(REPO_ROOT, "research", "v45", "reports"), exist_ok=True)
    
    out_json = os.path.join(REPO_ROOT, "research", "v45", "artifacts", "baseline_v44_lock.json")
    with open(out_json, "w") as f:
        json.dump({"summary": summary, "legs": legs_data}, f, indent=2)
    print(f"Detailed lock data saved to {out_json}")
    
    print("\n--- BASELINE REPRODUCTION SUMMARY ---")
    print(f"V44 Win Rate: {summary['v44_record']['win_rate']}% ({v44_wins}W / {v44_ties}T / {v44_losses}L)")
    print(f"V35 Win Rate: {summary['v35_record']['win_rate']}% ({v35_wins}W / {v35_ties}T / {v35_losses}L)")
    print(f"Mean Cash Delta vs V35: ${summary['mean_cash_delta_vs_v35']:>+7.2f}")
    print(f"Median Cash Delta vs V35: ${summary['median_cash_delta_vs_v35']:>+7.2f}")
    print(f"Rescues: {rescues} | Casualties: {casualties}")
    
    return summary


if __name__ == "__main__":
    run_baseline_benchmark()
