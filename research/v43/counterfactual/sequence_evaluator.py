# SPDX-License-Identifier: MIT
"""Kagriculture V43 Sequential Counterfactual Engine.

Evaluates short intervention sequences against baseline via exact terminal rollouts:
- Simulates exact branches to terminal step 719
- Evaluates isolated interventions: alpha(A), alpha(B)
- Evaluates composite sequence: alpha(A -> B)
- Calculates interaction value: interaction(A, B) = alpha(A -> B) - alpha(A) - alpha(B)
- Detects synergy (interaction > 0), anti-synergy (interaction < 0), rescues, and casualties
- Adheres to strict zero-leakage constraints (no seed or future leak)
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
from research.v43.executor.v43_executor import V43SafeExecutor, NUM_V43_INTERVENTIONS, V43_INTERVENTION_NAMES


class SequentialCounterfactualEvaluator:
    """Evaluates individual interventions and multi-step sequences via exact branch rollouts to terminal step."""

    def __init__(self):
        self.executor = V43SafeExecutor()

    def simulate_branch_to_terminal(
        self,
        sim: FastKagricultureSim,
        obs0: Dict[str, Any],
        obs1: Dict[str, Any],
        opp_master: Any,
        scheduled_interventions: Dict[int, int],  # step -> intervention_id
        player: int = 0
    ) -> Dict[str, Any]:
        """Simulates from current state to terminal step 719, applying scheduled interventions."""
        sim_branch = copy.deepcopy(sim)
        v35_branch = V43SafeExecutor()
        opp_branch = copy.deepcopy(opp_master)
        cur_obs0 = copy.deepcopy(obs0)
        cur_obs1 = copy.deepcopy(obs1)

        applied_actions = {}

        while not sim_branch.done:
            cur_step = int(cur_obs0.get("step", 0) or 0)
            target_action = scheduled_interventions.get(cur_step, 0)

            act0 = v35_branch.execute(target_action, cur_obs0, player=player)
            act1 = opp_branch(cur_obs1)

            if target_action != 0:
                applied_actions[cur_step] = target_action

            [cur_obs0, cur_obs1], _, _, _ = sim_branch.step([act0, act1])

        cash = float(cur_obs0.get("farms", [{}])[player].get("money", 0.0) or 0.0)
        opp_cash = float(cur_obs1.get("farms", [{}])[1 - player].get("money", 0.0) or 0.0)
        margin = cash - opp_cash
        win = margin > 0

        return {
            "cash": cash,
            "opp_cash": opp_cash,
            "margin": margin,
            "win": win,
            "applied_actions": applied_actions
        }

    def evaluate_sequence_pair(
        self,
        sim: FastKagricultureSim,
        obs0: Dict[str, Any],
        obs1: Dict[str, Any],
        opp_master: Any,
        step1: int,
        action1: int,
        step2: int,
        action2: int,
        player: int = 0
    ) -> Dict[str, Any]:
        """Evaluates baseline, A alone, B alone, and A -> B compound sequence."""
        # 1. Baseline branch (No interventions)
        base_res = self.simulate_branch_to_terminal(
            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp_master,
            scheduled_interventions={}, player=player
        )
        base_cash = base_res["cash"]
        base_margin = base_res["margin"]
        base_win = base_res["win"]

        # 2. Action A alone at step1
        res_a = self.simulate_branch_to_terminal(
            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp_master,
            scheduled_interventions={step1: action1}, player=player
        )
        alpha_a = res_a["cash"] - base_cash
        margin_delta_a = res_a["margin"] - base_margin
        rescue_a = (not base_win) and res_a["win"]
        casualty_a = base_win and (not res_a["win"])

        # 3. Action B alone at step2
        res_b = self.simulate_branch_to_terminal(
            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp_master,
            scheduled_interventions={step2: action2}, player=player
        )
        alpha_b = res_b["cash"] - base_cash
        margin_delta_b = res_b["margin"] - base_margin
        rescue_b = (not base_win) and res_b["win"]
        casualty_b = base_win and (not res_b["win"])

        # 4. Action A -> B composite sequence
        sched_ab = {step1: action1, step2: action2} if step1 != step2 else {step1: action1}
        res_ab = self.simulate_branch_to_terminal(
            sim=sim, obs0=obs0, obs1=obs1, opp_master=opp_master,
            scheduled_interventions=sched_ab, player=player
        )
        alpha_ab = res_ab["cash"] - base_cash
        margin_delta_ab = res_ab["margin"] - base_margin
        rescue_ab = (not base_win) and res_ab["win"]
        casualty_ab = base_win and (not res_ab["win"])

        # 5. Interaction effect
        interaction_cash = alpha_ab - (alpha_a + alpha_b)
        interaction_margin = margin_delta_ab - (margin_delta_a + margin_delta_b)
        is_synergistic = interaction_cash > 5.0
        is_anti_synergistic = interaction_cash < -5.0

        return {
            "step1": step1,
            "action1": action1,
            "name1": V43_INTERVENTION_NAMES[action1],
            "step2": step2,
            "action2": action2,
            "name2": V43_INTERVENTION_NAMES[action2],
            "base_cash": base_cash,
            "base_margin": base_margin,
            "base_win": base_win,
            "alpha_a": alpha_a,
            "alpha_b": alpha_b,
            "alpha_ab": alpha_ab,
            "interaction_cash": interaction_cash,
            "interaction_margin": interaction_margin,
            "is_synergistic": is_synergistic,
            "is_anti_synergistic": is_anti_synergistic,
            "rescue_a": rescue_a,
            "rescue_b": rescue_b,
            "rescue_ab": rescue_ab,
            "casualty_a": casualty_a,
            "casualty_b": casualty_b,
            "casualty_ab": casualty_ab,
        }
