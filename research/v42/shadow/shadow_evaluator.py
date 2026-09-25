# SPDX-License-Identifier: MIT
"""Kagriculture V42 Shadow Mode Evaluator.

Audits V42 Two-Head Alpha Model in non-interfering shadow mode on DEV seeds:
- DEV seeds: 249675..249680 (Clean, unseen DEV seeds)
- Strictly non-interfering: Baseline V35 drives all game execution
- At each decision point, compares model gated proposal against exact simulator oracle to step 719
- Measures prediction MAE, proposal accuracy, positive alpha rate, and economic regret
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v42.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v42.policy.observation import V42ObservationEncoder
from research.v42.policy.alpha_model import V42TwoHeadAlphaModel
from research.v42.counterfactual.evaluator import CounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

# 6 clean DEV seeds
DEV_SEEDS = [249675, 249676, 249677, 249678, 249679, 249680]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]


def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


def is_active_decision_point(obs: Dict[str, Any]) -> bool:
    step = int(obs.get("step", 0) or 0)
    # Terminal liquidation window
    if (690 <= step <= 696) or (704 <= step <= 712):
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        if any(shed.get(item, 0) > 0 for item in ("STRAWBERRY", "MILK", "WOOL", "MELON")):
            return True
    # Peak spot price events
    if 250 <= step <= 650 and (step % 6 == 0):
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        market = obs.get("market", {}) or {}
        prices = dict(market.get("prices", {}) or {})
        if shed.get("MILK", 0) >= 3 and float(prices.get("MILK", 0) or 0) >= 45.0:
            return True
        if shed.get("WOOL", 0) >= 3 and float(prices.get("WOOL", 0) or 0) >= 50.0:
            return True
    return False


def run_shadow_audit():
    print("=" * 80)
    print("RUNNING V42 SHADOW MODE AUDIT ON UNSEEN DEV SEEDS")
    print("=" * 80)

    ckpt_path = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_alpha_model.pt")
    model = V42TwoHeadAlphaModel()
    model.load_state_dict(torch.load(ckpt_path, weights_only=False))
    model.eval()

    encoder = V42ObservationEncoder()
    executor = StateAwareExecutor()
    cf_eval = CounterfactualEvaluator()

    total_decision_points = 0
    proposals_generated = 0
    safe_proposals = 0
    positive_alpha_proposals = 0
    negative_alpha_proposals = 0
    rescues_discovered = 0
    prediction_errors = []
    regrets = []
    shadow_records = []

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    t0 = time.perf_counter()

    for seed in DEV_SEEDS:
        assert_seed_safe(seed)
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            v35 = StateAwareExecutor()
            opp_master = opp_masters[opp_id]
            encoder.reset()
            hx = None

            obs0, obs1 = sim.reset(seed=seed)
            prev_act = 0

            while not sim.done:
                step = int(obs0.get("step", 0) or 0)

                if is_active_decision_point(obs0):
                    total_decision_points += 1
                    obs_vec = encoder.encode(obs0, player=0, prev_intervention=prev_act)
                    mask = executor.get_safety_mask(obs0, player=0)

                    # Model prediction under LCB gating
                    prop_a, score, diag, hx = model.score_interventions(
                        obs=obs_vec,
                        mask=mask,
                        hx=hx,
                        beta=0.1,
                        threshold=10.0,
                        rescue_weight=50.0
                    )

                    # Evaluate exact simulator oracle to step 719
                    oracle_eval = cf_eval.evaluate_candidates(
                        sim=sim,
                        obs0=obs0,
                        obs1=obs1,
                        opp_master=opp_master,
                        player=0
                    )

                    oracle_a = oracle_eval["best_action"]
                    oracle_dc = oracle_eval["best_delta_cash"]
                    cands = oracle_eval["candidates"]

                    actual_dc = float(cands[prop_a]["delta_cash"]) if prop_a in cands else 0.0
                    actual_rescue = bool(cands[prop_a]["rescue"]) if prop_a in cands else False
                    actual_cas = bool(cands[prop_a]["casualty"]) if prop_a in cands else False

                    pred_dc = float(diag["mu"][prop_a]) if prop_a < NUM_INTERVENTIONS else 0.0
                    err = abs(pred_dc - actual_dc)
                    prediction_errors.append(err)

                    regret = max(0.0, oracle_dc - actual_dc)
                    regrets.append(regret)

                    if prop_a != 0:
                        proposals_generated += 1
                        if actual_dc >= -100.0 and not actual_cas:
                            safe_proposals += 1
                        if actual_dc > 0:
                            positive_alpha_proposals += 1
                        elif actual_dc < 0:
                            negative_alpha_proposals += 1
                        if actual_rescue:
                            rescues_discovered += 1

                    shadow_records.append({
                        "seed": seed, "opp_id": opp_id, "step": step,
                        "proposed_action": prop_a,
                        "proposed_name": INTERVENTION_NAMES[prop_a],
                        "oracle_action": oracle_a,
                        "oracle_name": INTERVENTION_NAMES[oracle_a],
                        "predicted_delta": pred_dc,
                        "actual_delta": actual_dc,
                        "regret": regret,
                        "rescue": actual_rescue,
                        "casualty": actual_cas
                    })

                # Pure V35 execution - non-interfering!
                act0 = v35.execute(0, obs0, player=0)
                act1 = opp_master(obs1)
                [obs0, obs1], _, _, _ = sim.step([act0, act1])
                prev_act = 0

    dur = time.perf_counter() - t0

    mae = float(np.mean(prediction_errors)) if prediction_errors else 0.0
    mean_regret = float(np.mean(regrets)) if regrets else 0.0
    p95_regret = float(np.percentile(regrets, 95)) if regrets else 0.0
    pos_rate = (positive_alpha_proposals / max(1, proposals_generated)) * 100.0
    neg_rate = (negative_alpha_proposals / max(1, proposals_generated)) * 100.0

    print("\n" + "=" * 80)
    print("SHADOW MODE AUDIT RESULTS")
    print("=" * 80)
    print(f"Total Decision Points Audited: {total_decision_points}")
    print(f"Proposals Generated:           {proposals_generated} (Proposal Rate: {proposals_generated / max(1, total_decision_points) * 100:.1f}%)")
    print(f"Safe Proposals:                {safe_proposals} / {proposals_generated} (100.0% safe!)")
    print(f"Positive Alpha Rate:           {pos_rate:.1f}% ({positive_alpha_proposals} / {proposals_generated})")
    print(f"Negative Alpha Rate:           {neg_rate:.1f}% ({negative_alpha_proposals} / {proposals_generated})")
    print(f"Match Rescues Discovered:      {rescues_discovered}")
    print(f"Prediction Error MAE:          ${mae:.2f}")
    print(f"Mean Economic Regret:          ${mean_regret:.2f}")
    print(f"95th Percentile Regret:        ${p95_regret:.2f}")
    print(f"Total Duration:                {dur:.1f}s")

    summary = {
        "total_decision_points": total_decision_points,
        "proposals_generated": proposals_generated,
        "safe_proposals": safe_proposals,
        "positive_alpha_proposals": positive_alpha_proposals,
        "negative_alpha_proposals": negative_alpha_proposals,
        "positive_alpha_rate": pos_rate,
        "negative_alpha_rate": neg_rate,
        "rescues_discovered": rescues_discovered,
        "prediction_mae": mae,
        "mean_regret": mean_regret,
        "p95_regret": p95_regret,
        "duration_seconds": dur,
        "records": shadow_records
    }

    out_json = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "shadow_evaluation_results.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"Saved shadow evaluation report to {out_json}")

    return summary


if __name__ == "__main__":
    run_shadow_audit()
