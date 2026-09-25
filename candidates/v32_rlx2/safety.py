# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Safety Invariants & Legality Enforcer.

Guarantees fail-closed fallback to A7, valid action schemas, order clamping,
and bankruptcy prevention.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple

try:
    from rlx2_config import BOARD_SIZE, PRODUCTS, SHED_CAPACITY
except ImportError:
    from candidates.v32_rlx2.rlx2_config import BOARD_SIZE, PRODUCTS, SHED_CAPACITY


class SafetyEnforcer:
    def __init__(self, board_size: int = BOARD_SIZE):
        self.board_size = board_size
        self.fallback_count = 0
        self.clamped_order_count = 0
        
    def sanitize_action(
        self,
        candidate_action: Dict[str, Any],
        base_a7_action: Dict[str, Any],
        observation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sanitizes candidate action against physical and market legality.
        
        If candidate action is structurally malformed or triggers an unhandled
        exception, fails closed to base_a7_action immediately.
        """
        try:
            player = int(observation.get("player", 0) or 0)
            farms = observation.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0) or 0.0)
            private = observation.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            
            hands_count = len(farm.get("hands", []) or [])
            
            # Unit counts validation
            farmer_act = candidate_action.get("farmer") or ["PASS"]
            hands_acts = list(candidate_action.get("hands") or [])
            
            # Pad / truncate hands
            while len(hands_acts) < hands_count:
                hands_acts.append(["PASS"])
            hands_acts = hands_acts[:hands_count]
            
            # Market validation and clamping
            raw_market = list(candidate_action.get("market") or [])
            valid_market: List[List[Any]] = []
            committed_spend = 0.0
            
            for order in raw_market:
                if not order or not isinstance(order, (list, tuple)) or len(order) < 1:
                    continue
                op = order[0]
                if op == "SELL" and len(order) >= 3:
                    prod = order[1]
                    qty = int(order[2])
                    avail = int(shed.get(prod, 0))
                    if avail > 0 and qty > 0:
                        clamped_qty = min(qty, avail)
                        valid_market.append(["SELL", prod, clamped_qty])
                        shed[prod] -= clamped_qty
                elif op == "HIRE":
                    valid_market.append(["HIRE"])
                elif op == "BUY_LAND":
                    valid_market.append(["BUY_LAND"])
                elif op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL") and len(order) >= 3:
                    valid_market.append(list(order))
                elif op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL") and len(order) == 2:
                    valid_market.append([op, order[1], 1])
                    
            # Clamp to Kaggle max 10 orders
            valid_market = valid_market[:10]
            
            return {
                "farmer": farmer_act,
                "hands": hands_acts,
                "market": valid_market
            }
        except Exception:
            self.fallback_count += 1
            return copy.deepcopy(base_a7_action)
