# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Deterministic Executor.

Translates discrete macro strategic actions into concrete simulator actions.
Guarantees bit-identical execution for FOLLOW_A7 (Action 0) and fail-closed
safety across all deviation arms.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional

try:
    from action_space import ACTION_NAMES
    from rlx2_config import ANIMAL_COSTS, PRODUCTS, SEED_PRICES
    from safety import SafetyEnforcer
    from state import EconomicFeatures
except ImportError:
    from candidates.v32_rlx2.action_space import ACTION_NAMES
    from candidates.v32_rlx2.rlx2_config import ANIMAL_COSTS, PRODUCTS, SEED_PRICES
    from candidates.v32_rlx2.safety import SafetyEnforcer
    from candidates.v32_rlx2.state import EconomicFeatures


class StrategicExecutor:
    def __init__(self):
        self.safety = SafetyEnforcer()
        
    def execute(
        self,
        macro_action: int,
        observation: Dict[str, Any],
        features: EconomicFeatures,
        base_a7_action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes macro action index against observation and base A7 action."""
        # ACTION 0: FOLLOW_A7 (MANDATORY BIT-IDENTICAL IDENTITY)
        if macro_action == 0:
            return copy.deepcopy(base_a7_action)
            
        action = copy.deepcopy(base_a7_action)
        mkt = list(action.get("market") or [])
        
        # ACTION 1: OPPORTUNISTIC_SELL
        if macro_action == 1:
            existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
            for prod in PRODUCTS:
                qty = features.shed_inventory.get(prod, 0)
                px = features.spot_prices.get(prod, 0.0)
                if qty >= 4 and px >= 15.0 and prod not in existing_sells:
                    if len(mkt) < 10:
                        mkt.append(["SELL", prod, qty])
                        
        # ACTION 2: SELECTIVE_PREEMPT_SELL
        elif macro_action == 2:
            existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
            for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
                qty = features.shed_inventory.get(prod, 0)
                px = features.spot_prices.get(prod, 0.0)
                if qty >= 2 and px >= 25.0 and prod not in existing_sells:
                    if len(mkt) < 10:
                        mkt.append(["SELL", prod, qty])
                        
        # ACTION 3: LIQUIDATE_SURPLUS
        elif macro_action == 3:
            existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
            for prod in PRODUCTS:
                qty = features.shed_inventory.get(prod, 0)
                if prod == "WHEAT":
                    qty = max(0, qty - 15)  # Keep 15 wheat for animal feed
                if qty > 0 and prod not in existing_sells:
                    if len(mkt) < 10:
                        mkt.append(["SELL", prod, qty])
                        
        # ACTION 4: CROP_EXPANSION_MELON
        elif macro_action == 4:
            if features.cash >= SEED_PRICES["MELON"] and len(mkt) < 10:
                buy_qty = min(4, int(features.cash // SEED_PRICES["MELON"]))
                if buy_qty > 0:
                    mkt.append(["BUY_SEED", "MELON", buy_qty])
                    
        # ACTION 5: CROP_EXPANSION_WHEAT
        elif macro_action == 5:
            if features.cash >= SEED_PRICES["WHEAT"] and len(mkt) < 10:
                buy_qty = min(6, int(features.cash // SEED_PRICES["WHEAT"]))
                if buy_qty > 0:
                    mkt.append(["BUY_SEED", "WHEAT", buy_qty])
                    
        # ACTION 6: LIVESTOCK_EXPANSION_COW
        elif macro_action == 6:
            if features.cash >= ANIMAL_COSTS["COW"] and len(mkt) < 10:
                mkt.append(["BUY_ANIMAL", "COW", 1])
                
        # ACTION 7: LIVESTOCK_EXPANSION_SHEEP
        elif macro_action == 7:
            if features.cash >= ANIMAL_COSTS["SHEEP"] and len(mkt) < 10:
                mkt.append(["BUY_ANIMAL", "SHEEP", 1])
                
        # ACTION 8: PRESERVE_CASH
        elif macro_action == 8:
            # Throttle optional hires and land expansions
            mkt = [o for o in mkt if o and o[0] not in ("HIRE", "BUY_LAND")]
            
        # ACTION 9: EXPAND_LAND
        elif macro_action == 9:
            if features.cash >= features.next_land_cost and len(mkt) < 10:
                if not any(o and o[0] == "BUY_LAND" for o in mkt):
                    mkt.append(["BUY_LAND"])
                    
        action["market"] = mkt[:10]
        return self.safety.sanitize_action(action, base_a7_action, observation)
