# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Exact Simulator Strategic Search Engine.

Evaluates counterfactual macro strategic actions using exact forward rollouts
with A7 resumption, discovering high-consequence decision points and optimal
strategic targets.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from kaggle_environments import make

try:
    from action_space import ACTION_SPACE_SIZE, get_action_mask
    from rlx2_config import RLX2Config
    from executor import StrategicExecutor
    from opponents import load_league_opponent
    from state import EconomicFeatures, extract_economic_features, vectorize_features
except ImportError:
    from candidates.v32_rlx2.action_space import ACTION_SPACE_SIZE, get_action_mask
    from candidates.v32_rlx2.rlx2_config import RLX2Config
    from candidates.v32_rlx2.executor import StrategicExecutor
    from candidates.v32_rlx2.opponents import load_league_opponent
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features, vectorize_features


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


@dataclass
class StrategicTarget:
    seed: int
    opponent_id: str
    seat: int
    step: int
    state_vector: np.ndarray
    action_mask: np.ndarray
    a7_cash: float
    action_values: Dict[int, float]
    best_action: int
    best_cash: float
    best_delta: float
    second_best_action: int
    second_best_cash: float
    gap: float  # best_cash - second_best_cash


class StrategicSearchEngine:
    def __init__(self, config: Optional[RLX2Config] = None):
        self.cfg = config or RLX2Config()
        self.executor = StrategicExecutor()
        
    def evaluate_counterfactual(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        candidate_macro_action: int,
        macro_duration: int = 4
    ) -> float:
        """Simulates branch_step with candidate_macro_action, then resumes A7 until 719."""
        from scripts.v32_common import load_agent
        
        env = make("kaggriculture", configuration={"seed": seed})
        env.reset()
        
        a7 = load_agent("E9_AST")
        opp = load_league_opponent(opponent_id)
        
        step_idx = 0
        current_features = None
        
        while not env.done:
            p_obs = _get_shared_obs(env, seat)
            opp_obs = _get_shared_obs(env, 1 - seat)
            step_idx = int(p_obs.get("step", step_idx) or step_idx)
            
            base_a7 = a7.act(p_obs)
            opp_act = opp(opp_obs)
            
            if branch_step <= step_idx < branch_step + macro_duration and candidate_macro_action != 0:
                # Apply deviation
                current_features = extract_economic_features(p_obs, player=seat)
                p_act = self.executor.execute(
                    macro_action=candidate_macro_action,
                    observation=p_obs,
                    features=current_features,
                    base_a7_action=base_a7
                )
            else:
                # Normal A7 execution
                p_act = base_a7
                
            if seat == 0:
                env.step([p_act, opp_act])
            else:
                env.step([opp_act, p_act])
                
        final_cash = float(env.steps[-1][seat]["reward"] or 0.0)
        return final_cash
        
    def search_decision_state(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        macro_duration: int = 4
    ) -> StrategicTarget:
        """Runs counterfactual search over all legal macro actions at branch_step."""
        from scripts.v32_common import load_agent
        
        # 1. First run up to branch_step to extract exact economic state & mask
        env = make("kaggriculture", configuration={"seed": seed})
        env.reset()
        a7 = load_agent("E9_AST")
        opp = load_league_opponent(opponent_id)
        
        p_obs = None
        while not env.done:
            p_obs = _get_shared_obs(env, seat)
            opp_obs = _get_shared_obs(env, 1 - seat)
            cur_step = int(p_obs.get("step", 0) or 0)
            if cur_step >= branch_step:
                break
            act0 = a7.act(p_obs)
            act1 = opp(opp_obs)
            if seat == 0:
                env.step([act0, act1])
            else:
                env.step([act1, act0])
                
        features = extract_economic_features(p_obs, player=seat)
        mask = get_action_mask(features)
        state_vec = vectorize_features(features, tier=self.cfg.state_tier)
        
        # 2. Evaluate all legal candidate actions
        action_values = {}
        for a in range(ACTION_SPACE_SIZE):
            if mask[a]:
                val = self.evaluate_counterfactual(
                    seed=seed,
                    opponent_id=opponent_id,
                    seat=seat,
                    branch_step=branch_step,
                    candidate_macro_action=a,
                    macro_duration=macro_duration
                )
                action_values[a] = val
            else:
                action_values[a] = -1e9
                
        a7_val = action_values.get(0, 0.0)
        
        # Rank actions
        ranked = sorted(
            [(a, v) for a, v in action_values.items() if mask[a]],
            key=lambda x: x[1],
            reverse=True
        )
        
        best_a, best_v = ranked[0]
        second_a, second_v = ranked[1] if len(ranked) > 1 else (0, a7_val)
        
        return StrategicTarget(
            seed=seed,
            opponent_id=opponent_id,
            seat=seat,
            step=branch_step,
            state_vector=state_vec,
            action_mask=mask,
            a7_cash=a7_val,
            action_values=action_values,
            best_action=best_a,
            best_cash=best_v,
            best_delta=best_v - a7_val,
            second_best_action=second_a,
            second_best_cash=second_v,
            gap=best_v - second_v
        )
