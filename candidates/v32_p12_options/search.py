# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Exact Option Search Engine.

Evaluates candidate options using exact forward lookahead in the simulator,
measuring local delta (t+H), post-resync delta (t+H+24), and terminal cash
after returning to the A7 incumbent.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from kaggle_environments import make

try:
    from incumbent import A7Incumbent
    from option_library import OptionContract
    from option_executor import OptionExecutor
    from resync import ResyncState, SyncStatus, evaluate_resync
    from candidates.v32_rlx2.opponents import load_league_opponent
    from candidates.v32_rlx2.state import extract_economic_features
except ImportError:
    from candidates.v32_p12_options.incumbent import A7Incumbent
    from candidates.v32_p12_options.option_library import OptionContract
    from candidates.v32_p12_options.option_executor import OptionExecutor
    from candidates.v32_p12_options.resync import ResyncState, SyncStatus, evaluate_resync
    from candidates.v32_rlx2.opponents import load_league_opponent
    from candidates.v32_rlx2.state import extract_economic_features


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


@dataclass
class OptionEvaluationResult:
    option_id: str
    candidate_action: int
    step: int
    local_delta: float
    resync_delta: float
    terminal_delta: float
    a7_terminal_cash: float
    cand_terminal_cash: float
    post_opt_sync: ResyncState
    post_resync_sync: ResyncState


class OptionSearchEngine:
    """Exact simulator search engine for evaluating sparse options."""
    def __init__(self, resync_window: int = 24):
        self.resync_window = resync_window

    def evaluate_option(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        option: OptionContract,
        known_a7_terminal_cash: Optional[float] = None
    ) -> OptionEvaluationResult:
        """Evaluates an option against baseline A7 continuation."""
        from scripts.v32_common import load_agent
        
        post_opt_step = min(719, branch_step + option.duration)
        resync_step = min(719, branch_step + option.duration + self.resync_window)

        # 1. Baseline A7 (if not already cached)
        env_a7 = make("kaggriculture", configuration={"seed": seed})
        env_a7.reset()
        a7_agent = load_agent("E9_AST")
        opp_a7 = load_league_opponent(opponent_id)

        obs_a7_post_opt = None
        obs_a7_resync = None

        while not env_a7.done:
            p_obs = _get_shared_obs(env_a7, seat)
            opp_obs = _get_shared_obs(env_a7, 1 - seat)
            step = int(p_obs.get("step", 0) or 0)

            if step == post_opt_step:
                obs_a7_post_opt = copy.deepcopy(p_obs)
            elif step == resync_step:
                obs_a7_resync = copy.deepcopy(p_obs)

            act_p = a7_agent.act(p_obs)
            act_opp = opp_a7(opp_obs)
            if seat == 0:
                env_a7.step([act_p, act_opp])
            else:
                env_a7.step([act_opp, act_p])

        final_cash_a7 = float(env_a7.steps[-1][seat]["reward"] or 0.0)

        # 2. Candidate Simulation (A7 -> Option H ticks -> A7)
        env_cand = make("kaggriculture", configuration={"seed": seed})
        env_cand.reset()
        a7_cand = load_agent("E9_AST")
        opp_cand = load_league_opponent(opponent_id)
        executor = OptionExecutor()

        obs_cand_post_opt = None
        obs_cand_resync = None

        while not env_cand.done:
            p_obs = _get_shared_obs(env_cand, seat)
            opp_obs = _get_shared_obs(env_cand, 1 - seat)
            step = int(p_obs.get("step", 0) or 0)

            if step == post_opt_step:
                obs_cand_post_opt = copy.deepcopy(p_obs)
            elif step == resync_step:
                obs_cand_resync = copy.deepcopy(p_obs)

            base_a7 = a7_cand.act(p_obs)
            act_opp = opp_cand(opp_obs)

            if step == branch_step:
                executor.start_option(option, step)

            if executor.is_active:
                features = extract_economic_features(p_obs, player=seat)
                act_p, _ = executor.execute_step(p_obs, features, base_a7)
            else:
                act_p = base_a7

            if seat == 0:
                env_cand.step([act_p, act_opp])
            else:
                env_cand.step([act_opp, act_p])

        final_cash_cand = float(env_cand.steps[-1][seat]["reward"] or 0.0)

        # 3. Compute Deltas & Synchronization
        cash_a7_post = float(obs_a7_post_opt.get("farms", [{}, {}])[seat].get("money", 0.0) or 0.0) if obs_a7_post_opt else 0.0
        cash_cand_post = float(obs_cand_post_opt.get("farms", [{}, {}])[seat].get("money", 0.0) or 0.0) if obs_cand_post_opt else 0.0
        local_delta = cash_cand_post - cash_a7_post

        cash_a7_res = float(obs_a7_resync.get("farms", [{}, {}])[seat].get("money", 0.0) or 0.0) if obs_a7_resync else 0.0
        cash_cand_res = float(obs_cand_resync.get("farms", [{}, {}])[seat].get("money", 0.0) or 0.0) if obs_cand_resync else 0.0
        resync_delta = cash_cand_res - cash_a7_res

        terminal_delta = final_cash_cand - final_cash_a7

        resync_post = evaluate_resync(post_opt_step, obs_cand_post_opt, obs_a7_post_opt, player=seat)
        resync_after = evaluate_resync(resync_step, obs_cand_resync, obs_a7_resync, player=seat)

        return OptionEvaluationResult(
            option_id=option.option_id,
            candidate_action=option.candidate_action,
            step=branch_step,
            local_delta=local_delta,
            resync_delta=resync_delta,
            terminal_delta=terminal_delta,
            a7_terminal_cash=final_cash_a7,
            cand_terminal_cash=final_cash_cand,
            post_opt_sync=resync_post,
            post_resync_sync=resync_after
        )
