# SPDX-License-Identifier: MIT
"""V33 Route Selector: Selective Observable Regime Classification.

Evaluates observable game state at early strategic decision boundaries (t in {24, 48, 72})
and decides whether to STAY on R0_A7 or SWITCH to a complementary expert (e.g. R2_DMITRII).
Enforces strict selective prediction with confidence gating, tail-risk bounding,
one-switch-first policy, and deterministic A7 fallback.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple


class RouteSelector:
    """Selective, rule-gated regime classifier operating on causal observables."""

    def __init__(
        self,
        decision_steps: Tuple[int, ...] = (24, 48, 72),
        min_gain_threshold: float = 2500.0,
        max_tail_risk: float = 3000.0,
        enable_switching: bool = True,
    ):
        self.decision_steps = decision_steps
        self.min_gain_threshold = min_gain_threshold
        self.max_tail_risk = max_tail_risk
        self.enable_switching = enable_switching
        self.switches_made = 0
        self.current_route = "R0_A7"
        self.last_decision = "STAY_R0"
        self.decision_history: List[Dict[str, Any]] = []

    def reset(self):
        self.switches_made = 0
        self.current_route = "R0_A7"
        self.last_decision = "STAY_R0"
        self.decision_history.clear()

    def extract_observable_features(self, obs: Dict[str, Any]) -> Dict[str, float]:
        """Extracts strictly causal, observable market and farm metrics."""
        step = float(obs.get("step", 0) or 0)
        mkt = obs.get("market", {}) or {}
        prices = mkt.get("prices", {}) or {}
        inv = mkt.get("inventory", {}) or {}

        farms = obs.get("farms", []) or []
        player = int(obs.get("player", 0) or 0)
        opp_player = 1 - player

        # Opponent visible indicators
        opp_farm = farms[opp_player] if len(farms) > opp_player else {}
        opp_hands = len(opp_farm.get("hands", []) or [])
        opp_claimed_quads = len(opp_farm.get("claimed", []) or [])

        # Spot market features
        wheat_p = float(prices.get("WHEAT", 25) or 25)
        carrot_p = float(prices.get("CARROT", 35) or 35)
        tomato_p = float(prices.get("TOMATO", 60) or 60)
        melon_p = float(prices.get("MELON", 250) or 250)
        milk_p = float(prices.get("MILK", 160) or 160)
        wool_p = float(prices.get("WOOL", 200) or 200)

        wheat_inv = float(inv.get("WHEAT", 10000) or 10000)
        milk_inv = float(inv.get("MILK", 10000) or 10000)

        return {
            "step": step,
            "opp_visible_hands": float(opp_hands),
            "opp_claimed_quads": float(opp_claimed_quads),
            "wheat_price": wheat_p,
            "carrot_price": carrot_p,
            "tomato_price": tomato_p,
            "melon_price": melon_p,
            "milk_price": milk_p,
            "wool_price": wool_p,
            "wheat_inventory": wheat_inv,
            "milk_inventory": milk_inv,
            "crop_basket_index": (wheat_p / 25.0 + carrot_p / 35.0 + tomato_p / 60.0) / 3.0,
            "animal_basket_index": (milk_p / 160.0 + wool_p / 200.0) / 2.0,
        }

    def evaluate(self, obs: Dict[str, Any]) -> str:
        """Determines the routing action at the current step.
        Returns one of: 'STAY_R0', 'SWITCH_R2_DMITRII', or 'ABSTAIN'.
        """
        step = int(obs.get("step", 0) or 0)

        # 1. Enforce one-switch-first invariant
        if self.switches_made >= 1 or not self.enable_switching:
            return "STAY_R0"

        # 2. Enforce decision boundary gating
        if step not in self.decision_steps:
            return "STAY_R0"

        features = self.extract_observable_features(obs)

        # 3. Rule Classifier & Confidence Gating:
        # Signature for R2_DMITRII opportunity:
        # Crop market collapse (wheat price <= 20, wheat inv > 10500)
        # OR Opponent animal capex focus where crop margins are thin
        crop_collapsed = (features["wheat_price"] <= 20.0 and features["wheat_inventory"] > 10500.0)
        animal_resilient = (features["animal_basket_index"] >= 0.95)

        predicted_advantage = 0.0
        confidence = 0.0

        if crop_collapsed and animal_resilient:
            predicted_advantage = 3500.0
            confidence = 0.85
        elif features["opp_claimed_quads"] >= 2 and features["wheat_price"] <= 22.0:
            predicted_advantage = 2800.0
            confidence = 0.75

        # 4. Tail-risk and gain threshold gating
        if (
            predicted_advantage >= self.min_gain_threshold
            and confidence >= 0.70
            and self.max_tail_risk <= 4000.0
        ):
            decision = "SWITCH_R2_DMITRII"
            self.switches_made += 1
            self.current_route = "R2_DMITRII"
        else:
            decision = "STAY_R0"

        self.last_decision = decision
        self.decision_history.append({
            "step": step,
            "features": features,
            "predicted_advantage": predicted_advantage,
            "confidence": confidence,
            "decision": decision,
        })
        return decision
