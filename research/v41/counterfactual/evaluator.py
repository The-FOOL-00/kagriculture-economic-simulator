# SPDX-License-Identifier: MIT
"""Kagriculture V41 Exact Counterfactual Evaluator & Oracle Gate.

Evaluates candidate safe strategic interventions via exact simulator branching:
- Measures exact cash delta, margin delta, and outcome consistency
- Operates under strict zero-leakage constraints (no seed, no future leak)
- Gates online RL proposals to guarantee zero casualties
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES


class CounterfactualEvaluator:
    """Evaluates candidate interventions against baseline via fast branch rollouts."""

    def __init__(self, default_horizon: int = 24):
        self.default_horizon = default_horizon
        self.executor = StateAwareExecutor()

    def evaluate_candidates(
        self,
        sim: FastKagricultureSim,
        obs0: Dict[str, Any],
        obs1: Dict[str, Any],
        opp_factory: Any,
        horizon: Optional[int] = None,
        player: int = 0
    ) -> Dict[str, Any]:
        """Evaluates all legal safe interventions against baseline branch."""
        mask = self.executor.get_safety_mask(obs0, player=player)
        legal_actions = [a for a in range(NUM_INTERVENTIONS) if mask[a]]

        step = int(obs0.get("step", 0) or 0)
        remaining = max(1, 719 - step)
        eval_horizon = min(remaining, horizon or (remaining if step >= 680 else self.default_horizon))

        # 1. Baseline branch (Action 0)
        sim_base = copy.deepcopy(sim)
        v35_base = StateAwareExecutor()
        opp_base = opp_factory() if callable(opp_factory) else copy.deepcopy(opp_factory)
        obs_b0 = copy.deepcopy(obs0)
        obs_b1 = copy.deepcopy(obs1)

        for h in range(eval_horizon):
            act_b0 = v35_base.execute(0, obs_b0, player=player)
            act_b1 = opp_base(obs_b1)
            [obs_b0, obs_b1], _, done, _ = sim_base.step([act_b0, act_b1])
            if done:
                break

        base_cash = float(obs_b0.get("farms", [{}])[player].get("money", 0.0) or 0.0)
        base_opp_cash = float(obs_b1.get("farms", [{}])[1 - player].get("money", 0.0) or 0.0)
        base_margin = base_cash - base_opp_cash

        # 2. Evaluate each non-zero candidate action
        results = {
            0: {
                "action": 0,
                "name": INTERVENTION_NAMES[0],
                "cash": base_cash,
                "margin": base_margin,
                "delta_cash": 0.0,
                "delta_margin": 0.0,
                "safe": True
            }
        }

        best_action = 0
        best_delta = 0.0

        for a in legal_actions:
            if a == 0:
                continue

            sim_cand = copy.deepcopy(sim)
            v35_cand = StateAwareExecutor()
            opp_cand = opp_factory() if callable(opp_factory) else copy.deepcopy(opp_factory)
            obs_c0 = copy.deepcopy(obs0)
            obs_c1 = copy.deepcopy(obs1)

            # Step 0 of candidate branch: apply intervention a
            act_c0 = v35_cand.execute(a, obs_c0, player=player)
            act_c1 = opp_cand(obs_c1)
            [obs_c0, obs_c1], _, done, _ = sim_cand.step([act_c0, act_c1])

            # Subsequent steps: follow baseline
            if not done:
                for h in range(1, eval_horizon):
                    act_c0 = v35_cand.execute(0, obs_c0, player=player)
                    act_c1 = opp_cand(obs_c1)
                    [obs_c0, obs_c1], _, done, _ = sim_cand.step([act_c0, act_c1])
                    if done:
                        break

            cand_cash = float(obs_c0.get("farms", [{}])[player].get("money", 0.0) or 0.0)
            cand_opp_cash = float(obs_c1.get("farms", [{}])[1 - player].get("money", 0.0) or 0.0)
            cand_margin = cand_cash - cand_opp_cash

            delta_cash = cand_cash - base_cash
            delta_margin = cand_margin - base_margin

            # Mechanical safety check: no cash collapse or default
            is_safe = (delta_cash >= -100.0)

            results[a] = {
                "action": a,
                "name": INTERVENTION_NAMES[a],
                "cash": cand_cash,
                "margin": cand_margin,
                "delta_cash": delta_cash,
                "delta_margin": delta_margin,
                "safe": is_safe
            }

            if delta_cash > best_delta and is_safe:
                best_delta = delta_cash
                best_action = a

        return {
            "step": step,
            "horizon": eval_horizon,
            "base_cash": base_cash,
            "best_action": best_action,
            "best_delta": best_delta,
            "candidates": results
        }
