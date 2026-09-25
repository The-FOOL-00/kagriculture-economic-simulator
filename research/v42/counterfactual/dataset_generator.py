# SPDX-License-Identifier: MIT
"""Kagriculture V42 Counterfactual Dataset Generator.

Active mining of exact incremental alpha across safe training seeds:
- Safe training seeds: 249635..249670 (Strict Zero-Touch on protected holdouts)
- Prioritizes baseline losses, near-ties, and high-delta terminal liquidation regimes
- Evaluates exact counterfactual rollouts to terminal step 719
- Mines hard negatives (actions that look profitable locally but degrade terminal outcome)
"""

from __future__ import annotations
import copy
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
from research.v42.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v42.policy.observation import V42ObservationEncoder, OBSERVATION_DIM
from research.v42.counterfactual.evaluator import CounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

# 24 safe training seeds (including verified loss and near-tie seeds)
TRAIN_SEEDS = [
    249635, 249636, 249637, 249638, 249639, 249640,
    249641, 249642, 249643, 249644, 249645, 249646,
    249647, 249648, 249649, 249650, 249651, 249652,
    249653, 249654, 249655, 249656, 249657, 249659
]

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
    """Event-triggered decision points prioritizing high-impact and rescue regimes."""
    step = int(obs.get("step", 0) or 0)

    # 1. Terminal liquidation window (steps 690..714, high rescue density)
    if (690 <= step <= 696) or (704 <= step <= 712):
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        if any(shed.get(item, 0) > 0 for item in ("STRAWBERRY", "MILK", "WOOL", "MELON")):
            return True

    # 2. Peak spot price events with substantial inventory
    if 250 <= step <= 650 and (step % 6 == 0):
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        market = obs.get("market", {}) or {}
        prices = dict(market.get("prices", {}) or {})

        if shed.get("MILK", 0) >= 3 and float(prices.get("MILK", 0) or 0) >= 40.0:
            return True
        if shed.get("WOOL", 0) >= 3 and float(prices.get("WOOL", 0) or 0) >= 45.0:
            return True
        if shed.get("STRAWBERRY", 0) >= 4 and float(prices.get("STRAWBERRY", 0) or 0) >= 30.0:
            return True

    # 3. Market depression events (hard negative mining for HOLD action)
    if 300 <= step <= 600 and (step % 12 == 0):
        market = obs.get("market", {}) or {}
        prices = dict(market.get("prices", {}) or {})
        if any(float(prices.get(item, 20) or 20) < 18.0 for item in ("MILK", "WOOL", "STRAWBERRY")):
            return True

    # 4. Critical liquidity boundary events
    farms = obs.get("farms", [{}])
    cash = float(farms[0].get("money", 0.0) if farms else 0.0)
    if cash < 500.0 and step < 680 and (step % 12 == 0):
        return True

    return False


def generate_v42_dataset(max_seeds: int = 16, max_opponents: int = 4) -> Dict[str, Any]:
    print(f"Generating V42 counterfactual dataset across {max_seeds} seeds and {max_opponents} opponents...")
    t0 = time.perf_counter()

    encoder = V42ObservationEncoder()
    executor = StateAwareExecutor()
    cf_eval = CounterfactualEvaluator()

    dataset_samples = []
    seeds_used = TRAIN_SEEDS[:max_seeds]
    opps_used = OPPONENTS[:max_opponents]

    total_decision_points = 0
    positive_alpha_points = 0
    rescue_points = 0

    # Preload master opponents to avoid disk re-loading
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in opps_used}

    for seed in seeds_used:
        assert_seed_safe(seed)
        for opp_id in opps_used:
            sim = FastKagricultureSim(seed=seed)
            v35 = StateAwareExecutor()
            opp_master = opp_masters[opp_id]
            encoder.reset()

            obs0, obs1 = sim.reset(seed=seed)
            prev_act = 0

            while not sim.done:
                step = int(obs0.get("step", 0) or 0)

                if is_active_decision_point(obs0):
                    total_decision_points += 1
                    obs_vec = encoder.encode(obs0, player=0, prev_intervention=prev_act)
                    mask = executor.get_safety_mask(obs0, player=0)

                    # Exact simulator counterfactual evaluation to step 719
                    eval_res = cf_eval.evaluate_candidates(
                        sim=sim,
                        obs0=obs0,
                        obs1=obs1,
                        opp_master=opp_master,
                        player=0
                    )

                    cands = eval_res["candidates"]
                    best_a = eval_res["best_action"]
                    best_dc = eval_res["best_delta_cash"]
                    best_dm = eval_res["best_delta_margin"]
                    base_win = eval_res["base_win"]

                    delta_cash_vec = np.zeros(NUM_INTERVENTIONS, dtype=np.float32)
                    delta_margin_vec = np.zeros(NUM_INTERVENTIONS, dtype=np.float32)
                    rescue_vec = np.zeros(NUM_INTERVENTIONS, dtype=bool)
                    casualty_vec = np.zeros(NUM_INTERVENTIONS, dtype=bool)

                    for a in range(NUM_INTERVENTIONS):
                        if a in cands:
                            delta_cash_vec[a] = float(cands[a]["delta_cash"])
                            delta_margin_vec[a] = float(cands[a]["delta_margin"])
                            rescue_vec[a] = bool(cands[a]["rescue"])
                            casualty_vec[a] = bool(cands[a]["casualty"])
                        else:
                            delta_cash_vec[a] = -9999.0
                            delta_margin_vec[a] = -9999.0

                    if best_dc > 0.0 and best_a != 0:
                        positive_alpha_points += 1
                    if any(rescue_vec):
                        rescue_points += 1

                    sample = {
                        "obs": obs_vec,
                        "mask": mask,
                        "delta_cash": delta_cash_vec,
                        "delta_margin": delta_margin_vec,
                        "rescue": rescue_vec,
                        "casualty": casualty_vec,
                        "base_win": base_win,
                        "base_margin": eval_res["base_margin"],
                        "best_action": best_a,
                        "best_delta_cash": best_dc,
                        "best_delta_margin": best_dm,
                        "step": step,
                        "seed": seed,
                        "opp_id": opp_id
                    }
                    dataset_samples.append(sample)

                # Advance baseline step
                act0 = v35.execute(0, obs0, player=0)
                act1 = opp_master(obs1)
                [obs0, obs1], _, _, _ = sim.step([act0, act1])
                prev_act = 0

    dur = time.perf_counter() - t0
    print(f"\nGenerated {len(dataset_samples)} transitions across {len(seeds_used)} seeds in {dur:.1f}s.")
    print(f"Positive Alpha Points: {positive_alpha_points} / {total_decision_points} ({positive_alpha_points / max(1, total_decision_points) * 100:.1f}%)")
    print(f"Rescue Decision Points: {rescue_points} / {total_decision_points} ({rescue_points / max(1, total_decision_points) * 100:.1f}%)")

    # Save artifact
    out_path = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "v42_alpha_dataset.pt")
    torch.save(dataset_samples, out_path)
    print(f"Saved V42 alpha dataset to {out_path}")

    return {
        "num_samples": len(dataset_samples),
        "total_decision_points": total_decision_points,
        "positive_alpha_points": positive_alpha_points,
        "rescue_points": rescue_points,
        "duration": dur,
        "out_path": out_path
    }


if __name__ == "__main__":
    generate_v42_dataset(max_seeds=16, max_opponents=4)
