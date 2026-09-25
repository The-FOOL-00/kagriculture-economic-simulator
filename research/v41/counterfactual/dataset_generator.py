# SPDX-License-Identifier: MIT
"""Kagriculture V41 Counterfactual Dataset Generator.

Mines exact counterfactual action deltas across safe training seeds:
- Safe training seeds only: 249635..249654
- Opponent diversity: E8_DMITRII, E2_A7, E0_V3, SYN_AGG
- Strict Zero-Touch on protected holdouts (214200..214249, 340090..340199, 249695..249734)
"""

from __future__ import annotations
import os
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v41.policy.observation import V41ObservationEncoder, OBSERVATION_DIM
from research.v41.counterfactual.evaluator import CounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

# Safe training seeds
TRAIN_SEEDS = list(range(249635, 249655))  # 20 safe seeds
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


def is_strategic_decision_point(obs: Dict[str, Any]) -> bool:
    """Event-triggered gate for when strategic intervention should be evaluated."""
    step = int(obs.get("step", 0) or 0)

    # 1. Terminal window
    if step in (692, 693, 694) or step >= 710:
        return True

    # 2. Mid-game land window
    if 280 <= step <= 312 and step % 4 == 0:
        farms = obs.get("farms", [{}])
        cash = float(farms[0].get("money", 0.0) if farms else 0.0)
        if cash >= 10000.0:
            return True

    # 3. Peak spot price with inventory in shed
    private = obs.get("private", {}) or {}
    shed = dict(private.get("shed", {}) or {})
    market = obs.get("market", {}) or {}
    prices = dict(market.get("prices", {}) or {})

    for item, min_p in [("MILK", 30.0), ("WOOL", 35.0), ("STRAWBERRY", 25.0), ("MELON", 35.0)]:
        if shed.get(item, 0) >= 2 and float(prices.get(item, 0.0) or 0.0) >= min_p:
            if step % 6 == 0:
                return True

    return False


def generate_dataset(num_seeds: int = 12, max_opponents: int = 3) -> Dict[str, Any]:
    print(f"Generating counterfactual dataset across {num_seeds} seeds...")
    t0 = time.perf_counter()

    encoder = V41ObservationEncoder()
    executor = StateAwareExecutor()
    cf_eval = CounterfactualEvaluator(default_horizon=24)

    dataset_samples = []
    seeds_used = TRAIN_SEEDS[:num_seeds]
    opps_used = OPPONENTS[:max_opponents]

    total_decision_points = 0
    positive_interventions_found = 0

    for seed in seeds_used:
        assert_seed_safe(seed)
        for opp_id in opps_used:
            sim = FastKagricultureSim(seed=seed)
            v35 = StateAwareExecutor()
            opp = load_league_opponent(opp_id)
            encoder.reset()

            obs0, obs1 = sim.reset(seed=seed)
            prev_act = 0

            while not sim.done:
                step = int(obs0.get("step", 0) or 0)

                # Check if strategic decision point
                if is_strategic_decision_point(obs0):
                    total_decision_points += 1
                    obs_vec = encoder.encode(obs0, player=0, prev_intervention=prev_act)
                    mask = executor.get_safety_mask(obs0, player=0)

                    # Evaluate exact counterfactual branches
                    eval_res = cf_eval.evaluate_candidates(
                        sim=sim,
                        obs0=obs0,
                        obs1=obs1,
                        opp_factory=lambda: load_league_opponent(opp_id),
                        player=0
                    )

                    best_a = eval_res["best_action"]
                    best_d = eval_res["best_delta"]
                    cands = eval_res["candidates"]

                    # Delta vector across all interventions
                    deltas = np.zeros(NUM_INTERVENTIONS, dtype=np.float32)
                    for a_idx in range(NUM_INTERVENTIONS):
                        if a_idx in cands:
                            deltas[a_idx] = float(cands[a_idx]["delta_cash"])
                        else:
                            deltas[a_idx] = -9999.0  # illegal

                    if best_d > 0.0 and best_a != 0:
                        positive_interventions_found += 1

                    dataset_samples.append({
                        "obs": obs_vec,
                        "mask": mask,
                        "deltas": deltas,
                        "best_action": best_a,
                        "best_delta": best_d,
                        "step": step,
                        "seed": seed,
                        "opp_id": opp_id
                    })

                # Step simulation forward with baseline
                act0 = v35.execute(0, obs0, player=0)
                act1 = opp(obs1)
                [obs0, obs1], _, _, _ = sim.step([act0, act1])
                prev_act = 0

    dur = time.perf_counter() - t0
    print(f"Generated {len(dataset_samples)} counterfactual transitions in {dur:.1f}s.")
    print(f"Positive alpha interventions: {positive_interventions_found} / {total_decision_points} ({positive_interventions_found / max(1, total_decision_points) * 100:.1f}%)")

    # Save artifact
    out_path = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "counterfactual_dataset.pt")
    torch.save(dataset_samples, out_path)
    print(f"Saved dataset to {out_path}")

    return {
        "num_samples": len(dataset_samples),
        "total_decision_points": total_decision_points,
        "positive_interventions": positive_interventions_found,
        "duration": dur,
        "out_path": out_path
    }


if __name__ == "__main__":
    generate_dataset(num_seeds=10, max_opponents=3)
