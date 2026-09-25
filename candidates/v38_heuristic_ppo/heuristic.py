# SPDX-License-Identifier: MIT
"""Kagriculture V38 Strong Deterministic Expert Heuristic.

Serves as the foundational 'safe action generator'.
Combines:
1. V35 opening wash (25/25 WHEAT) for guaranteed working capital preservation.
2. A7 exact physical choreography and route-replay chassis.
3. Closed-loop economic safety checks (liquidity preservation, terminal liquidation).
4. Deterministic macro execution interface with fail-closed fallback to base behavior.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    from config import REPO_ROOT, PRODUCTS, SEED_PRICES, ANIMAL_COSTS, MIN_LIQUID_CASH_BUFFER
    from state_features import StateAbstraction, extract_state_abstraction
    from physical_planner import PhysicalPlanner
except ImportError:
    from candidates.v38_heuristic_ppo.config import REPO_ROOT, PRODUCTS, SEED_PRICES, ANIMAL_COSTS, MIN_LIQUID_CASH_BUFFER
    from candidates.v38_heuristic_ppo.state_features import StateAbstraction, extract_state_abstraction
    from candidates.v38_heuristic_ppo.physical_planner import PhysicalPlanner

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent


class V38DeterministicExpert:
    """Strong closed-loop deterministic expert with fail-closed safety."""
    
    def __init__(self, wash_buy: int = 25, wash_sell: int = 25):
        self.wash_buy = wash_buy
        self.wash_sell = wash_sell
        self.a7_agent = load_agent("E9_AST")
        self.physical_planner = PhysicalPlanner()
        self.prev_econ = None
        self.step_count = 0
        
    def reset(self):
        self.a7_agent = load_agent("E9_AST")
        self.prev_econ = None
        self.step_count = 0

    def get_base_action(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates the foundational V35/A7 expert action."""
        step = int(observation.get("step", 0) or 0)
        
        # 1. Base A7 action from frozen engine
        try:
            base_act = self.a7_agent.act(observation, configuration)
        except Exception:
            base_act = {"farmer": ["PASS"], "hands": [], "market": []}
            
        # 2. Step 0: V35 25/25 opening wash optimization
        if step == 0:
            act = copy.deepcopy(base_act)
            if self.wash_buy == 0 and self.wash_sell == 0:
                act["market"] = []
            else:
                act["market"] = [
                    ["BUY_PRODUCT", "WHEAT", self.wash_buy],
                    ["SELL", "WHEAT", self.wash_sell]
                ]
            return act
            
        # 3. Steps 714..718: Guaranteed terminal liquidation
        if step >= 714:
            act = copy.deepcopy(base_act)
            mkt = list(act.get("market") or [])
            priv = observation.get("private", {}) or {}
            shed = priv.get("shed", {}) or {}
            existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
            for prod, qty in shed.items():
                if qty > 0 and prod not in existing_sells and len(mkt) < 10:
                    mkt.append(["SELL", prod, qty])
            act["market"] = mkt[:10]
            return act
            
        return base_act

    def act(
        self,
        observation: Dict[str, Any],
        macro_option: int = 0,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generates action under macro option guidance.
        
        If macro_option == 0 (TRUST_HEURISTIC): returns base expert action.
        If macro_option > 0: executes bounded macro option with fail-closed fallback.
        """
        base_action = self.get_base_action(observation, configuration)
        if macro_option == 0:
            return base_action
            
        try:
            # Extract state for validation
            player = int(observation.get("player", 0) or 0)
            state_abs = extract_state_abstraction(observation, player=player, prev_econ=self.prev_econ)
            self.prev_econ = state_abs.economic
            
            # Apply macro modification through fail-closed execution
            from candidates.v38_heuristic_ppo.macro_options import execute_macro_option
            modified_action, success = execute_macro_option(
                macro_option=macro_option,
                base_action=base_action,
                state=state_abs,
                observation=observation
            )
            
            if success:
                return modified_action
            return base_action
        except Exception:
            # Strict fail-closed fallback
            return base_action
