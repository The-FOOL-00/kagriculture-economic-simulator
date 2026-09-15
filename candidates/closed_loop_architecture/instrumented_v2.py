"""
INSTRUMENTED CLOSED LOOP AGENT V2
Faithful instrumented baseline with explicit telemetry and additive action hooks.
Default mode is strictly IDENTICAL to ClosedLoopAgentV2.
"""
import copy
import json
import os
import sys
from typing import Dict, List, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from closed_loop_v2 import ClosedLoopAgentV2

class InstrumentedClosedLoopAgentV2(ClosedLoopAgentV2):
    def __init__(
        self,
        jit_headroom_threshold: int = 96,
        base_liquidity_reserve: float = 500.0,
        enable_market_timing: bool = True,
        enable_additive_option: bool = False,
        additive_policy: Optional[Any] = None
    ):
        super().__init__(
            jit_headroom_threshold=jit_headroom_threshold,
            base_liquidity_reserve=base_liquidity_reserve,
            enable_market_timing=enable_market_timing
        )
        self.enable_additive_option = enable_additive_option
        self.additive_policy = additive_policy
        self.action_history = []
        self.telemetry = {
            "additive_plants": 0,
            "additive_waters": 0,
            "additive_harvests": 0,
            "additive_sells": 0,
            "displaced_v2_actions": 0
        }

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Generate base V2 action
        action = super().act(obs)
        
        # 2. If additive option is active, apply overlay
        if self.enable_additive_option and self.additive_policy is not None:
            action = self.additive_policy.apply(obs, action, self)
            
        return action
