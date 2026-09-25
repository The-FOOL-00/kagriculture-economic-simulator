# SPDX-License-Identifier: MIT
"""Kagriculture V41 League Evaluator & A/B Ladder Benchmark Harness.

Executes exact 4-leg paired evaluations across candidate ladders and baselines:
- Measures Paired Win Rate, Mean & Median Cash Margins
- Tracks Rescues (Candidate wins where Baseline lost)
- Tracks Casualties (Candidate loses where Baseline won)
- Enforces strict seat symmetry and fresh-seed separation
- Guarantees Zero-Touch on protected holdout seed ranges
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v32_rlx2.opponents import load_league_opponent
from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v41.policy.observation import V41ObservationEncoder, OBSERVATION_DIM
from research.v41.policy.model import V41TemporalStrategicPolicy

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


def run_single_match(
    agent_0: Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]],
    agent_1: Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]],
    seed: int
) -> Tuple[float, float, float]:
    assert_seed_safe(seed)
    t0 = time.perf_counter()
    sim = FastKagricultureSim(seed=seed)
    obs0, obs1 = sim.reset(seed=seed)

    while not sim.done:
        act0 = agent_0(obs0)
        act1 = agent_1(obs1)
        [obs0, obs1], rewards, done, info = sim.step([act0, act1])

    dur = time.perf_counter() - t0
    r0 = float(sim.state[0].reward or 0.0)
    r1 = float(sim.state[1].reward or 0.0)
    return r0, r1, dur


def run_paired_matchup(
    candidate_fn_factory: Callable[[], Any],
    baseline_fn_factory: Callable[[], Any],
    opponent_id: str,
    seed: int
) -> Dict[str, Any]:
    assert_seed_safe(seed)

    # Leg 1: Candidate (Seat 0) vs Opponent (Seat 1)
    cand_0 = candidate_fn_factory()
    opp_1 = load_league_opponent(opponent_id)
    c_r0, o_r1, _ = run_single_match(cand_0, opp_1, seed)
    cand_win_seat0 = 1.0 if c_r0 > o_r1 else (0.5 if c_r0 == o_r1 else 0.0)

    # Leg 2: Baseline (Seat 0) vs Opponent (Seat 1)
    base_0 = baseline_fn_factory()
    opp_1_b = load_league_opponent(opponent_id)
    b_r0, ob_r1, _ = run_single_match(base_0, opp_1_b, seed)
    base_win_seat0 = 1.0 if b_r0 > ob_r1 else (0.5 if b_r0 == ob_r1 else 0.0)

    # Leg 3: Opponent (Seat 0) vs Candidate (Seat 1)
    opp_0 = load_league_opponent(opponent_id)
    cand_1 = candidate_fn_factory()
    o_r0, c_r1, _ = run_single_match(opp_0, cand_1, seed)
    cand_win_seat1 = 1.0 if c_r1 > o_r0 else (0.5 if c_r1 == o_r0 else 0.0)

    # Leg 4: Opponent (Seat 0) vs Baseline (Seat 1)
    opp_0_b = load_league_opponent(opponent_id)
    base_1 = baseline_fn_factory()
    ob_r0, b_r1, _ = run_single_match(opp_0_b, base_1, seed)
    base_win_seat1 = 1.0 if b_r1 > ob_r0 else (0.5 if b_r0 == ob_r1 else 0.0)

    mean_cand_cash = (c_r0 + c_r1) / 2.0
    mean_base_cash = (b_r0 + b_r1) / 2.0
    cash_delta = mean_cand_cash - mean_base_cash

    cand_wins = (1 if cand_win_seat0 == 1.0 else 0) + (1 if cand_win_seat1 == 1.0 else 0)
    base_wins = (1 if base_win_seat0 == 1.0 else 0) + (1 if base_win_seat1 == 1.0 else 0)

    # Casualties: Baseline won, but Candidate lost/tied
    casualties = 0
    if base_win_seat0 == 1.0 and cand_win_seat0 < 1.0:
        casualties += 1
    if base_win_seat1 == 1.0 and cand_win_seat1 < 1.0:
        casualties += 1

    # Rescues: Baseline lost/tied, but Candidate won
    rescues = 0
    if base_win_seat0 < 1.0 and cand_win_seat0 == 1.0:
        rescues += 1
    if base_win_seat1 < 1.0 and cand_win_seat1 == 1.0:
        rescues += 1

    return {
        "seed": seed,
        "opponent": opponent_id,
        "cand_cash_seat0": c_r0,
        "opp_cash_seat0": o_r1,
        "base_cash_seat0": b_r0,
        "cand_win_seat0": cand_win_seat0,
        "base_win_seat0": base_win_seat0,
        "cand_cash_seat1": c_r1,
        "opp_cash_seat1": o_r0,
        "base_cash_seat1": b_r1,
        "cand_win_seat1": cand_win_seat1,
        "base_win_seat1": base_win_seat1,
        "mean_cand_cash": mean_cand_cash,
        "mean_base_cash": mean_base_cash,
        "cash_delta": cash_delta,
        "cand_wins": cand_wins,
        "base_wins": base_wins,
        "rescues": rescues,
        "casualties": casualties
    }


def make_v41_agent(model_path: Optional[str] = None, confidence_threshold: float = 50.0) -> Callable:
    """Factory creating full V41 runtime agent."""
    executor = StateAwareExecutor()
    encoder = V41ObservationEncoder()

    if model_path and os.path.exists(model_path):
        policy = V41TemporalStrategicPolicy(
            obs_dim=OBSERVATION_DIM,
            hidden_dim=128,
            num_actions=NUM_INTERVENTIONS
        )
        ckpt = torch.load(model_path, map_location="cpu")
        if "model_state_dict" in ckpt:
            policy.load_state_dict(ckpt["model_state_dict"])
        else:
            policy.load_state_dict(ckpt)
        policy.eval()
    else:
        policy = None

    class _V41Agent:
        def __init__(self):
            self.executor = StateAwareExecutor()
            self.encoder = V41ObservationEncoder()
            self.policy = policy
            self.hx = self.policy.init_hidden(1, device=torch.device("cpu")) if self.policy else None
            self.conf_thresh = confidence_threshold

        def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            step = int(obs.get("step", 0) or 0)
            if step == 0:
                self.executor.reset()
                self.encoder.reset()
                if self.policy:
                    self.hx = self.policy.init_hidden(1, device=torch.device("cpu"))

            if self.policy:
                obs_vec = self.encoder.encode(obs, player=0)
                mask = self.executor.get_safety_mask(obs, player=0)
                action_idx, q_val, self.hx = self.policy.select_intervention(
                    obs_vec=obs_vec,
                    action_mask=mask,
                    hx=self.hx,
                    confidence_threshold=self.conf_thresh,
                    device="cpu"
                )
            else:
                action_idx = 0

            return self.executor.execute(action_idx, obs, cfg, player=0)

    return _V41Agent()
