# SPDX-License-Identifier: MIT
"""Kagriculture V38 Counterfactual Rollout Engine.

Computes exact forward simulation counterfactuals:
At decision step t, executes candidate macro option a for H steps,
then resumes the V38 deterministic expert until step 719.
Returns exact counterfactual advantage: A(s, a) = C_T(a) - C_T(heuristic).
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
from kaggle_environments import make

try:
    from config import (
        MACRO_ACTIONS, NUM_MACRO_ACTIONS, assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from heuristic import V38DeterministicExpert
    from macro_options import execute_macro_option, get_macro_action_mask
    from state_features import StateAbstraction, extract_state_abstraction, vectorize_economic_features
except ImportError:
    from candidates.v38_heuristic_ppo.config import (
        MACRO_ACTIONS, NUM_MACRO_ACTIONS, assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from candidates.v38_heuristic_ppo.heuristic import V38DeterministicExpert
    from candidates.v38_heuristic_ppo.macro_options import execute_macro_option, get_macro_action_mask
    from candidates.v38_heuristic_ppo.state_features import (
        StateAbstraction, extract_state_abstraction, vectorize_economic_features
    )

from candidates.v32_rlx2.opponents import load_league_opponent


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


class CounterfactualEngine:
    """Evaluates counterfactual branches using exact forward simulation."""
    
    def __init__(self, default_horizon: int = DEFAULT_MACRO_HORIZON):
        self.default_horizon = default_horizon
        
    def evaluate_branch(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        macro_option: int,
        horizon: int = 4
    ) -> Tuple[float, float]:
        """Runs exact rollout: applies macro_option at branch_step for horizon turns,
        then resumes V38 expert until step 719.
        
        Returns:
            (cand_terminal_cash, opp_terminal_cash)
        """
        assert_seed_safe(seed)
        
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        
        expert = V38DeterministicExpert()
        opp_fn = load_league_opponent(opponent_id)
        
        step_idx = 0
        prev_econ = None
        
        while not env.done:
            p_obs = _get_shared_obs(env, seat)
            opp_obs = _get_shared_obs(env, 1 - seat)
            step_idx = int(p_obs.get("step", step_idx) or step_idx)
            
            # Base expert action
            base_act = expert.get_base_action(p_obs)
            opp_act = opp_fn(opp_obs)
            
            # Decide whether this step is within the intervention window
            if branch_step <= step_idx < (branch_step + horizon) and macro_option != 0:
                state_abs = extract_state_abstraction(p_obs, player=seat, prev_econ=prev_econ)
                prev_econ = state_abs.economic
                cand_act, success = execute_macro_option(
                    macro_option=macro_option,
                    base_action=base_act,
                    state=state_abs,
                    observation=p_obs
                )
                p_act = cand_act if success else base_act
            else:
                p_act = base_act
                
            if seat == 0:
                env.step([p_act, opp_act])
            else:
                env.step([opp_act, p_act])
                
        c_cash = float(env.steps[-1][seat]["reward"] or 0.0)
        o_cash = float(env.steps[-1][1 - seat]["reward"] or 0.0)
        return c_cash, o_cash

    def evaluate_all_options_at_state(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        horizon: int = 4
    ) -> Dict[str, Any]:
        """Evaluates heuristic (Option 0) vs all legal macro options at branch_step."""
        assert_seed_safe(seed)
        
        # 1. First get state at branch_step by running up to branch_step
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        expert = V38DeterministicExpert()
        opp_fn = load_league_opponent(opponent_id)
        
        step_idx = 0
        prev_econ = None
        while not env.done and step_idx < branch_step:
            p_obs = _get_shared_obs(env, seat)
            opp_obs = _get_shared_obs(env, 1 - seat)
            step_idx = int(p_obs.get("step", step_idx) or step_idx)
            if step_idx >= branch_step:
                break
            p_act = expert.get_base_action(p_obs)
            opp_act = opp_fn(opp_obs)
            if seat == 0:
                env.step([p_act, opp_act])
            else:
                env.step([opp_act, p_act])
                
        # Capture decision state
        p_obs = _get_shared_obs(env, seat)
        state_abs = extract_state_abstraction(p_obs, player=seat, prev_econ=prev_econ)
        mask = get_macro_action_mask(state_abs)
        state_vec = vectorize_economic_features(state_abs.economic, state_abs.physical)
        
        # 2. Evaluate Baseline Heuristic (Option 0)
        h_cash, h_opp_cash = self.evaluate_branch(
            seed=seed, opponent_id=opponent_id, seat=seat,
            branch_step=branch_step, macro_option=0, horizon=horizon
        )
        
        option_results = {0: h_cash}
        advantages = {0: 0.0}
        
        # 3. Evaluate each legal candidate option
        best_opt = 0
        best_cash = h_cash
        best_delta = 0.0
        
        for opt in range(1, NUM_MACRO_ACTIONS):
            if not mask[opt]:
                continue
            cand_cash, _ = self.evaluate_branch(
                seed=seed, opponent_id=opponent_id, seat=seat,
                branch_step=branch_step, macro_option=opt, horizon=horizon
            )
            option_results[opt] = cand_cash
            delta = cand_cash - h_cash
            advantages[opt] = delta
            if delta > best_delta:
                best_delta = delta
                best_opt = opt
                best_cash = cand_cash
                
        return {
            "seed": seed,
            "opponent": opponent_id,
            "seat": seat,
            "step": branch_step,
            "horizon": horizon,
            "state_vector": state_vec.tolist(),
            "action_mask": mask.tolist(),
            "heuristic_cash": h_cash,
            "option_cash": option_results,
            "advantages": advantages,
            "best_option": best_opt,
            "best_cash": best_cash,
            "best_delta": best_delta,
        }
