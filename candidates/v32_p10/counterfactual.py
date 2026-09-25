# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Exact Counterfactual Simulator.

Evaluates candidate residual deviations using exact, simulator-grounded short/medium
horizon rollout comparisons:
    Baseline Branch: continue A7
    Counterfactual Branch: apply 1 residual action, then resume A7
Under identical simulator states and seeds.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kaggle_environments import make
from candidates.v32_p10.incumbent import load_fresh_a7


def _extract_asset_value(farm: Dict[str, Any], prices: Dict[str, float]) -> float:
    cash = float(farm.get("money", 0.0) or 0.0)
    return cash


class ExactCounterfactualEngine:
    def __init__(self, seed: int, episode_steps: int = 720):
        self.seed = seed
        self.episode_steps = episode_steps

    def evaluate_step_intervention(
        self,
        base_match_history: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        trigger_step: int,
        player: int,
        candidate_action: Dict[str, Any],
        opp_callable: Any,
        horizon: int = 8
    ) -> Dict[str, Any]:
        """Rolls out baseline vs counterfactual from step 0 up to trigger_step + horizon.
        
        Because kaggle_environments is deterministic given a seed and action sequence,
        we can replay actions up to trigger_step, then branch.
        """
        end_step = min(self.episode_steps, trigger_step + horizon)
        
        # 1. Baseline: Rollout A7 all the way through end_step
        env_base = make("kaggriculture", configuration={"seed": self.seed, "episodeSteps": end_step + 1}, debug=False)
        a7_base = load_fresh_a7()
        opp_base = opp_callable()
        agents_base = [a7_base, opp_base] if player == 0 else [opp_base, a7_base]
        env_base.run(agents_base)
        
        base_terminal_cash = float(env_base.steps[-1][player]["reward"] or 0.0)
        
        # 2. Counterfactual: Replay A7 up to trigger_step, inject candidate_action at trigger_step, then resume A7
        env_cf = make("kaggriculture", configuration={"seed": self.seed, "episodeSteps": end_step + 1}, debug=False)
        a7_cf = load_fresh_a7()
        opp_cf = opp_callable()
        
        # Custom agent that injects candidate_action at trigger_step
        def _cf_agent(obs, cfg=None):
            s = int(obs.get("step", 0) or 0)
            if s == trigger_step:
                return copy.deepcopy(candidate_action)
            return a7_cf(obs, cfg)
            
        agents_cf = [_cf_agent, opp_cf] if player == 0 else [opp_cf, _cf_agent]
        env_cf.run(agents_cf)
        
        cf_terminal_cash = float(env_cf.steps[-1][player]["reward"] or 0.0)
        delta = cf_terminal_cash - base_terminal_cash
        
        return {
            "trigger_step": trigger_step,
            "horizon": horizon,
            "baseline_cash": base_terminal_cash,
            "counterfactual_cash": cf_terminal_cash,
            "paired_delta": delta
        }
