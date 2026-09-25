# SPDX-License-Identifier: MIT
"""Kagriculture V34 Opportunity Detector & Search Gate (Distilled Policy).

Distills exact-search outcomes into an observable-only gating model.
Evaluates current state, A7 intended action, and market signals to decide whether:
1. STAY_A7: Condition is ordinary, execute A7 directly.
2. SEARCH: High-value opportunity detected, execute local forward search.
3. OVERRIDE: Validated, zero-risk tactical candidate triggered directly.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple

from candidates.v34_a7_tactical.tactical_types import (
    TacticalCandidate, PromotionStatus
)
from candidates.v34_a7_tactical.opponent_behavior_features import (
    OpponentBehaviorTracker, OpponentBehaviorSnapshot
)
from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard


class OpportunityDetector:
    """Observable search gate operating on spot prices and farm state."""

    def __init__(
        self,
        min_gain_threshold: float = 100.0,
        max_tail_risk: float = 100.0,
        enable_overrides: bool = True,
    ):
        self.min_gain_threshold = min_gain_threshold
        self.max_tail_risk = max_tail_risk
        self.enable_overrides = enable_overrides
        self.tracker = OpponentBehaviorTracker()
        self.liquidity_guard = LiquidityGuard()

    def reset(self):
        self.tracker.reset()

    def evaluate_opportunity(
        self,
        obs: Dict[str, Any],
        a7_action: Dict[str, Any],
    ) -> Tuple[str, Optional[Dict[str, Any]], float]:
        """Evaluates whether the current A7 decision point warrants a tactical override or search.

        Returns: (decision_type, override_action_or_none, confidence)
        decision_type is one of: 'STAY_A7', 'SEARCH', 'OVERRIDE'
        """
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        farm = farms[player] if len(farms) > player else {}
        cash = float(farm.get("money", 0.0) or 0.0)

        # Update observable behavioral features
        snap = self.tracker.update(obs)

        # 1. Gate: Step 0 Wash Opportunity
        if step == 0:
            wheat_p = snap.current_prices.get("WHEAT", 25.0)
            # When wheat spot price is at baseline (25.0), wash sizing 25/25 is validated safe
            if 20.0 <= wheat_p <= 30.0:
                act = copy.deepcopy(a7_action)
                act["market"] = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
                return "OVERRIDE", act, 0.95
            return "STAY_A7", None, 0.50

        # 2. Gate: Late-Game Planting Cutoff (step >= 680)
        if step >= 680:
            units = [a7_action.get("farmer", ["PASS"])] + list(a7_action.get("hands", []) or [])
            remaining_steps = 718 - step
            futile_crop_present = False
            for u in units:
                if u and u[0] == "PLANT" and len(u) >= 2:
                    crop = u[1]
                    growth_needed = {"WHEAT": 12, "CARROT": 24, "TOMATO": 48, "STRAWBERRY": 72, "MELON": 96}.get(crop, 24)
                    if growth_needed > remaining_steps:
                        futile_crop_present = True
                        break

            if futile_crop_present:
                act = copy.deepcopy(a7_action)
                cleaned_farmer = ["PASS"] if (act.get("farmer") and act["farmer"][0] == "PLANT") else act.get("farmer", ["PASS"])
                cleaned_hands = [["PASS"] if (h and h[0] == "PLANT") else h for h in (act.get("hands", []) or [])]
                act["farmer"] = cleaned_farmer
                act["hands"] = cleaned_hands
                # Filter seed buys
                act["market"] = [o for o in (act.get("market") or []) if not (o and o[0] == "BUY_SEED")]
                return "OVERRIDE", act, 0.98

        # Default: STAY_A7
        return "STAY_A7", None, 0.0
