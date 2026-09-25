# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Strategic Macro Environment.

Wraps the Kaggle simulation into a clean gym-like multi-step macro environment.
Supports variable macro-intervals (default H=4), discrete strategic actions,
action masking, opponent league swapping, and verified bit-identical parity.
"""

from __future__ import annotations
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from kaggle_environments import make

try:
    from action_space import ACTION_SPACE_SIZE, get_action_mask
    from rlx2_config import EPISODE_STEPS, RLX2Config
    from executor import StrategicExecutor
    from opponents import load_league_opponent
    from rewards import compute_step_reward
    from state import EconomicFeatures, extract_economic_features, vectorize_features
except ImportError:
    from candidates.v32_rlx2.action_space import ACTION_SPACE_SIZE, get_action_mask
    from candidates.v32_rlx2.rlx2_config import EPISODE_STEPS, RLX2Config
    from candidates.v32_rlx2.executor import StrategicExecutor
    from candidates.v32_rlx2.opponents import load_league_opponent
    from candidates.v32_rlx2.rewards import compute_step_reward
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features, vectorize_features


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    """Extracts complete shared observation for player pos."""
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


class RLX2Env:
    """Strategic macro environment for Kagriculture RL-X2."""
    
    def __init__(self, config: Optional[RLX2Config] = None):
        self.cfg = config or RLX2Config()
        self.executor = StrategicExecutor()
        self.env: Any = None
        self.seed: int = 0
        self.opponent_id: str = "E2_A7"
        self.seat: int = 0
        
        self.a7_agent: Any = None
        self.opp_agent: Any = None
        
        self.current_features: Optional[EconomicFeatures] = None
        self.prev_features: Optional[EconomicFeatures] = None
        self.macro_step_count: int = 0
        self.done: bool = False
        
        # Telemetry
        self.a7_reference_cash: Optional[float] = None
        self.history_actions: List[int] = []
        
    def reset(
        self,
        seed: int = 249635,
        opponent_id: str = "E2_A7",
        seat: int = 0,
        a7_reference_cash: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Resets environment with specified seed and opponent."""
        from scripts.v32_common import load_agent
        
        self.seed = seed
        self.opponent_id = opponent_id
        self.seat = seat
        self.a7_reference_cash = a7_reference_cash
        self.history_actions = []
        self.macro_step_count = 0
        self.done = False
        
        # Load agents fresh per match
        self.a7_agent = load_agent("E9_AST")
        self.opp_agent = load_league_opponent(opponent_id)
        
        self.env = make("kaggriculture", configuration={"seed": seed})
        self.env.reset()
        
        obs = _get_shared_obs(self.env, self.seat)
        self.current_features = extract_economic_features(obs, player=self.seat)
        self.prev_features = None
        
        obs_vec = vectorize_features(self.current_features, tier=self.cfg.state_tier)
        mask = get_action_mask(self.current_features)
        return obs_vec, mask
        
    def step(self, macro_action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """Steps the environment forward by macro_interval turns using macro_action."""
        if self.done:
            raise RuntimeError("Cannot step a completed environment.")
            
        self.history_actions.append(macro_action)
        self.macro_step_count += 1
        
        sub_steps = 0
        while not self.env.done and sub_steps < self.cfg.macro_interval:
            sub_steps += 1
            p_obs = _get_shared_obs(self.env, self.seat)
            opp_obs = _get_shared_obs(self.env, 1 - self.seat)
            
            # 1. Base A7 baseline action
            base_a7 = self.a7_agent.act(p_obs)
            
            # 2. Opponent action
            opp_act = self.opp_agent(opp_obs)
            
            # 3. Deterministic Strategic Executor translates macro intent
            p_act = self.executor.execute(
                macro_action=macro_action,
                observation=p_obs,
                features=self.current_features,
                base_a7_action=base_a7
            )
            
            # 4. Advance simulator by 1 step
            if self.seat == 0:
                self.env.step([p_act, opp_act])
            else:
                self.env.step([opp_act, p_act])
                
            self.prev_features = self.current_features
            new_p_obs = _get_shared_obs(self.env, self.seat)
            self.current_features = extract_economic_features(
                new_p_obs,
                player=self.seat,
                prev_prices=self.prev_features.spot_prices if self.prev_features else None
            )
            
        self.done = self.env.done
        
        # Calculate terminal rewards and metrics
        final_cash = float(self.env.steps[-1][self.seat]["reward"] or 0.0)
        opp_cash = float(self.env.steps[-1][1 - self.seat]["reward"] or 0.0)
        
        step_reward = compute_step_reward(
            reward_mode=self.cfg.reward_mode,
            features=self.current_features,
            prev_features=self.prev_features,
            is_terminal=self.done,
            final_cash=final_cash,
            a7_final_cash=self.a7_reference_cash,
            opp_final_cash=opp_cash
        )
        
        next_obs_vec = vectorize_features(self.current_features, tier=self.cfg.state_tier)
        mask = get_action_mask(self.current_features)
        
        info = {
            "step": self.current_features.step,
            "final_cash": final_cash if self.done else None,
            "opp_cash": opp_cash if self.done else None,
            "delta_vs_a7": (final_cash - self.a7_reference_cash) if (self.done and self.a7_reference_cash is not None) else None,
            "action_mask": mask,
        }
        
        return next_obs_vec, step_reward, self.done, info
