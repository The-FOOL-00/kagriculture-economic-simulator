# SPDX-License-Identifier: MIT
"""Kagriculture V42 Exact Counterfactual Evaluator & Oracle Gate.

Evaluates candidate safe strategic interventions via exact simulator branching:
- Simulates to true terminal step 719 to capture full compounding and avoid horizon truncation errors
- Measures exact cash delta, margin delta, rescue generation, and casualty occurrence
- Operates under strict zero-leakage constraints (no seed, no future leak)
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v42.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES


class CounterfactualEvaluator:
    """Evaluates candidate interventions against baseline via fast branch rollouts to terminal step."""

    def __init__(self):
        self.executor = StateAwareExecutor()

    def evaluate_candidates(
        self,
        sim: FastKagricultureSim,
        obs0: Dict[str, Any],
        obs1: Dict[str, Any],
        opp_master: Any,
        player: int = 0
    ) -> Dict[str, Any]:
        """Evaluates all legal safe interventions against baseline branch to step 719."""
        mask = self.executor.get_safety_mask(obs0, player=player)
        legal_actions = [a for a in range(NUM_INTERVENTIONS) if mask[a]]

        step = int(obs0.get("step", 0) or 0)

        # 1. Baseline branch (Action 0) to terminal step 719
        sim_base = copy.deepcopy(sim)
        v35_base = StateAwareExecutor()
        opp_base = copy.deepcopy(opp_master)
        obs_b0 = copy.deepcopy(obs0)
        obs_b1 = copy.deepcopy(obs1)

        while not sim_base.done:
            act_b0 = v35_base.execute(0, obs_b0, player=player)
            act_b1 = opp_base(obs_b1)
            [obs_b0, obs_b1], _, _, _ = sim_base.step([act_b0, act_b1])

        base_cash = float(obs_b0.get("farms", [{}])[player].get("money", 0.0) or 0.0)
        base_opp_cash = float(obs_b1.get("farms", [{}])[1 - player].get("money", 0.0) or 0.0)
        base_margin = base_cash - base_opp_cash
        base_win = base_margin > 0

        # 2. Evaluate each legal non-zero candidate action
        results = {
            0: {
                "action": 0,
                "name": INTERVENTION_NAMES[0],
                "cash": base_cash,
                "margin": base_margin,
                "delta_cash": 0.0,
                "delta_margin": 0.0,
                "base_win": base_win,
                "cand_win": base_win,
                "rescue": False,
                "casualty": False,
                "safe": True
            }
        }

        best_action = 0
        best_delta_cash = 0.0
        best_delta_margin = 0.0

        for a in legal_actions:
            if a == 0:
                continue

            sim_cand = copy.deepcopy(sim)
            v35_cand = StateAwareExecutor()
            opp_cand = copy.deepcopy(opp_master)
            obs_c0 = copy.deepcopy(obs0)
            obs_c1 = copy.deepcopy(obs1)

            # Step 0 of candidate branch: apply intervention a
            act_c0 = v35_cand.execute(a, obs_c0, player=player)
            act_c1 = opp_cand(obs_c1)
            [obs_c0, obs_c1], _, done, _ = sim_cand.step([act_c0, act_c1])

            # Subsequent steps: follow baseline to step 719
            while not sim_cand.done:
                act_c0 = v35_cand.execute(0, obs_c0, player=player)
                act_c1 = opp_cand(obs_c1)
                [obs_c0, obs_c1], _, _, _ = sim_cand.step([act_c0, act_c1])

            cand_cash = float(obs_c0.get("farms", [{}])[player].get("money", 0.0) or 0.0)
            cand_opp_cash = float(obs_c1.get("farms", [{}])[1 - player].get("money", 0.0) or 0.0)
            cand_margin = cand_cash - cand_opp_cash
            cand_win = cand_margin > 0

            delta_cash = cand_cash - base_cash
            delta_margin = cand_margin - base_margin
            is_rescue = (not base_win) and cand_win
            is_casualty = base_win and (not cand_win)

            # Safety rule: reject if it causes a casualty or drops cash by more than $150
            is_safe = (not is_casualty) and (delta_cash >= -150.0)

            results[a] = {
                "action": a,
                "name": INTERVENTION_NAMES[a],
                "cash": cand_cash,
                "margin": cand_margin,
                "delta_cash": delta_cash,
                "delta_margin": delta_margin,
                "base_win": base_win,
                "cand_win": cand_win,
                "rescue": is_rescue,
                "casualty": is_casualty,
                "safe": is_safe
            }

            # If action rescues the game or provides positive alpha without casualty
            if (is_rescue or delta_cash > best_delta_cash) and is_safe:
                best_delta_cash = delta_cash
                best_delta_margin = delta_margin
                best_action = a

        return {
            "step": step,
            "base_cash": base_cash,
            "base_margin": base_margin,
            "base_win": base_win,
            "best_action": best_action,
            "best_delta_cash": best_delta_cash,
            "best_delta_margin": best_delta_margin,
            "candidates": results
        }
