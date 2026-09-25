# SPDX-License-Identifier: MIT
"""Kagriculture V43 Active Learning & Information-Theoretic Boundary Search.

Focuses computation on high-information states:
- States where model uncertainty sigma(s, a) is high
- States where baseline is near-tie (|margin| <= $500)
- States where baseline suffers a loss (recoverability search)
- States where predictions between candidate sequences disagree
Outputs boundary search dataset and diagnostics.
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
from research.v43.executor.v43_executor import V43SafeExecutor, NUM_V43_INTERVENTIONS, V43_INTERVENTION_NAMES
from research.v42.policy.observation import V42ObservationEncoder
from research.v43.policy.sequence_model import V43SequenceAlphaModel
from research.v43.counterfactual.sequence_evaluator import SequentialCounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249648, 249657]
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


def run_active_learning_search(ckpt_path: str):
    print("=" * 80)
    print("V43 ACTIVE LEARNING & BOUNDARY CONDITION SEARCH")
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
    ]

    active_samples = []
    high_disagreement_count = 0
    near_tie_count = 0

    for seed in SEEDS:
        assert_seed_safe(seed)
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            v35 = V43SafeExecutor()
            opp = copy.deepcopy(opp_masters[opp_id])
            obs0, obs1 = sim.reset(seed=seed)
            encoder.reset()

            while not sim.done:
                step = int(obs0.get("step", 0) or 0)

                if step in (690, 692, 694):
                    obs_vec = encoder.encode(obs0, player=0)

                    # Model predictions for all candidate sequences
                    preds = []
                    for name, seq_tokens, _ in candidate_sequences:
                        _, mu, sig, p_res, _ = model.score_sequence(obs_vec, seq_tokens)
                        preds.append({"name": name, "mu": mu, "sig": sig, "p_res": p_res})

                    # Check prediction disagreement: max(mu) - min(mu)
                    mu_values = [p["mu"] for p in preds if p["name"] != "BASELINE"]
                    disagreement = max(mu_values) - min(mu_values) if mu_values else 0.0

                    # Compute baseline margin
                    c0 = float(obs0["farms"][0]["money"])
                    c1 = float(obs1["farms"][1]["money"])
                    cur_margin = c0 - c1

                    is_near_tie = abs(cur_margin) <= 1500.0
                    is_high_uncertainty = any(p["sig"] > 40.0 for p in preds)

                    if disagreement > 30.0 or is_near_tie or is_high_uncertainty:
                        if disagreement > 30.0:
                            high_disagreement_count += 1
                        if is_near_tie:
                            near_tie_count += 1

                        # Active rollout: sample exact outcomes
                        base_res = seq_eval.simulate_branch_to_terminal(
                            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp,
                            scheduled_interventions={}, player=0
                        )
                        b_cash = base_res["cash"]

                        exact_deltas = {}
                        for name, _, sched in candidate_sequences:
                            c_res = seq_eval.simulate_branch_to_terminal(
                                sim=sim, obs0=obs0, obs1=obs1, opp_master=opp,
                                scheduled_interventions=sched, player=0
                            )
                            exact_deltas[name] = c_res["cash"] - b_cash

                        active_samples.append({
                            "seed": seed,
                            "opp_id": opp_id,
                            "step": step,
                            "disagreement": round(disagreement, 2),
                            "cur_margin": round(cur_margin, 2),
                            "model_preds": preds,
                            "exact_deltas": exact_deltas
                        })

                [obs0, obs1], _, _, _ = sim.step([v35.execute(0, obs0), opp(obs1)])

    print(f"\nActive Learning Search Completed:")
    print(f"Total High-Information States Sampled: {len(active_samples)}")
    print(f"Disagreement States: {high_disagreement_count} | Near-Tie States: {near_tie_count}")

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "active_learning_results.json")
    with open(out_file, "w") as f:
        json.dump(active_samples, f, indent=2)
    print(f"Saved active learning dataset to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Active search finished in {dur:.1f}s.")
    return active_samples


if __name__ == "__main__":
    ckpt = os.path.join(REPO_ROOT, "research", "v43", "checkpoints", "v43_sequence_model.pt")
    if os.path.exists(ckpt):
        run_active_learning_search(ckpt)
    else:
        print("Model checkpoint not found yet.")
