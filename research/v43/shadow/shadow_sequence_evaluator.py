# SPDX-License-Identifier: MIT
"""Kagriculture V43 Shadow Mode Sequence Evaluator & Oracle Benchmark.

Audits V43SequenceAlphaModel in pure non-interfering shadow mode on DEV seeds:
- Baseline V35 drives 100% of gameplay (Golden Property preserved, zero gameplay interference)
- Model proposes LCB-gated action sequence at active decision points
- Evaluator branches simulator to terminal step 719 to measure exact true delta and oracle agreement
- Strict zero-touch on protected holdout seed ranges
- Outputs research/v43/artifacts/shadow_evaluation_results.json
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from research.v43.executor.v43_executor import V43SafeExecutor, NUM_V43_INTERVENTIONS, V43_INTERVENTION_NAMES, MARKETABLE_COMMODITIES
from research.v42.policy.observation import V42ObservationEncoder
from research.v43.policy.sequence_model import V43SequenceAlphaModel
from research.v43.counterfactual.sequence_evaluator import SequentialCounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

# 6 clean unseen DEV seeds
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


def run_shadow_audit(ckpt_path: str, beta: float = 1.0, threshold: float = 15.0):
    print("=" * 80)
    print("V43 SHADOW MODE SEQUENCE AUDIT & ORACLE BENCHMARK")
    print("=" * 80)
    t0 = time.perf_counter()

    model = V43SequenceAlphaModel()
    model.load_state_dict(torch.load(ckpt_path, weights_only=False))
    model.eval()

    encoder = V42ObservationEncoder()
    seq_eval = SequentialCounterfactualEvaluator()
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    candidate_sequences = [
        ("BASELINE", [0, 0, 0], {}),
        ("STAGGERED_50_50", [2, 2, 0], {694: 2, 705: 2}),
        ("STAGGERED_40_60", [1, 3, 0], {694: 1, 705: 3}),
        ("STAGGERED_3STEP_FLUSH", [2, 2, 4], {694: 2, 705: 2, 716: 4}),
        ("PRESERVE_AND_LIQ", [8, 2, 0], {300: 8, 694: 2}),
    ]

    shadow_proposals = []
    total_decision_points = 0
    proposals_generated = 0
    safe_proposals = 0
    positive_proposals = 0
    rescues_discovered = 0
    casualties_generated = 0
    mae_errors = []
    regrets = []

    for seed in DEV_SEEDS:
        assert_seed_safe(seed)
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            base = V35OpeningController()
            opp = copy.deepcopy(opp_masters[opp_id])
            obs0, obs1 = sim.reset(seed=seed)
            encoder.reset()

            while not sim.done:
                step = int(obs0.get("step", 0) or 0)

                # Active decision points
                is_decision_point = (
                    step in (690, 692, 694) or
                    (step == 300 and float(obs0["farms"][0]["money"]) < 1500.0)
                )

                if is_decision_point:
                    total_decision_points += 1
                    obs_vec = encoder.encode(obs0, player=0)

                    # Score each sequence under LCB
                    best_seq_name = "BASELINE"
                    best_sched = {}
                    best_lcb = 0.0
                    best_mu = 0.0
                    best_sig = 0.0

                    for name, seq_tokens, sched in candidate_sequences:
                        lcb, mu, sig, p_res, acc = model.score_sequence(
                            obs_vec, seq_tokens, beta=beta, threshold=threshold
                        )
                        if acc and lcb > best_lcb:
                            best_lcb = lcb
                            best_mu = mu
                            best_sig = sig
                            best_seq_name = name
                            best_sched = sched

                    # Exact baseline rollout
                    base_res = seq_eval.simulate_branch_to_terminal(
                        sim=sim, obs0=obs0, obs1=obs1, opp_master=opp,
                        scheduled_interventions={}, player=0
                    )
                    b_cash = base_res["cash"]
                    b_win = base_res["win"]

                    # Evaluate all candidate sequences to find true oracle
                    oracle_best_delta = 0.0
                    for name, _, sched in candidate_sequences:
                        c_res = seq_eval.simulate_branch_to_terminal(
                            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp,
                            scheduled_interventions=sched, player=0
                        )
                        d_c = c_res["cash"] - b_cash
                        if d_c > oracle_best_delta:
                            oracle_best_delta = d_c

                    if best_seq_name != "BASELINE":
                        proposals_generated += 1
                        cand_res = seq_eval.simulate_branch_to_terminal(
                            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp,
                            scheduled_interventions=best_sched, player=0
                        )
                        realized_dc = cand_res["cash"] - b_cash
                        is_rescue = (not b_win) and cand_res["win"]
                        is_cas = b_win and (not cand_res["win"])

                        error = abs(best_mu - realized_dc)
                        mae_errors.append(error)
                        regret = max(0.0, oracle_best_delta - realized_dc)
                        regrets.append(regret)

                        if realized_dc > 0:
                            positive_proposals += 1
                        if is_rescue:
                            rescues_discovered += 1
                        if is_cas:
                            casualties_generated += 1
                        else:
                            safe_proposals += 1

                        shadow_proposals.append({
                            "seed": seed,
                            "opp_id": opp_id,
                            "step": step,
                            "proposed_sequence": best_seq_name,
                            "predicted_mu": round(best_mu, 2),
                            "predicted_sigma": round(best_sig, 2),
                            "lcb_score": round(best_lcb, 2),
                            "realized_delta_cash": round(realized_dc, 2),
                            "oracle_delta_cash": round(oracle_best_delta, 2),
                            "regret": round(regret, 2),
                            "rescue": is_rescue,
                            "casualty": is_cas
                        })

                # Always execute baseline V35 in primary trajectory
                [obs0, obs1], _, _, _ = sim.step([base.act(obs0), opp(obs1)])

    mean_mae = float(np.mean(mae_errors)) if mae_errors else 0.0
    mean_regret = float(np.mean(regrets)) if regrets else 0.0
    med_regret = float(np.median(regrets)) if regrets else 0.0
    p95_regret = float(np.percentile(regrets, 95)) if regrets else 0.0

    print(f"\nTotal Strategic Decision Points: {total_decision_points}")
    print(f"Proposals Generated: {proposals_generated} ({proposals_generated / max(1, total_decision_points) * 100:.1f}%)")
    print(f"Safety Rate: {safe_proposals} / {proposals_generated} (Casualties: {casualties_generated})")
    print(f"Positive Delta Rate: {positive_proposals} / {proposals_generated} ({positive_proposals / max(1, proposals_generated) * 100:.1f}%)")
    print(f"Match Rescues: {rescues_discovered}")
    print(f"Prediction MAE: ${mean_mae:.2f}")
    print(f"Mean Regret: ${mean_regret:.2f} (Median: ${med_regret:.2f}, P95: ${p95_regret:.2f})")

    results_payload = {
        "total_decision_points": total_decision_points,
        "proposals_generated": proposals_generated,
        "proposal_rate_pct": round(proposals_generated / max(1, total_decision_points) * 100.0, 1),
        "safety_rate_pct": round(safe_proposals / max(1, proposals_generated) * 100.0, 1) if proposals_generated > 0 else 100.0,
        "positive_alpha_rate_pct": round(positive_proposals / max(1, proposals_generated) * 100.0, 1) if proposals_generated > 0 else 0.0,
        "casualties": casualties_generated,
        "rescues": rescues_discovered,
        "prediction_mae": round(mean_mae, 2),
        "mean_regret": round(mean_regret, 2),
        "median_regret": round(med_regret, 2),
        "p95_regret": round(p95_regret, 2),
        "proposals": shadow_proposals
    }

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "shadow_evaluation_results.json")
    with open(out_file, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"Shadow evaluation results saved to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Shadow evaluation completed in {dur:.1f}s.")
    return results_payload


if __name__ == "__main__":
    ckpt = os.path.join(REPO_ROOT, "research", "v43", "checkpoints", "v43_sequence_model.pt")
    if os.path.exists(ckpt):
        run_shadow_audit(ckpt)
    else:
        print("Checkpoint not found yet; will be run after model training.")
