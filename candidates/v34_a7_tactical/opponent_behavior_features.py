# SPDX-License-Identifier: MIT
"""Kagriculture V34 Opponent Behavior & Market Feature Extractor.

Extracts strictly causal, observable-only features without opponent identity,
seed ID, or future state leakage. Classifies observed opponent behavioral regimes
(e.g., crop saturation, livestock pressure, aggressive dumping) from spot prices
and public board observables.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

FORBIDDEN_KEYS = {
    "final_reward",
    "final_cash",
    "terminal_score",
    "winner",
    "delta",
    "match_result",
    "future_price",
    "future_action",
    "opponent_name",
    "opponent_id",
    "opponent_rating",
    "seed",
}

COMMODITIES = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
BASE_PRICES = {
    "WHEAT": 25.0,
    "CARROT": 35.0,
    "TOMATO": 60.0,
    "STRAWBERRY": 120.0,
    "MELON": 250.0,
    "EGG": 50.0,
    "MILK": 160.0,
    "WOOL": 200.0,
    "FERTILIZER": 100.0,
}


@dataclass
class OpponentBehaviorSnapshot:
    """Strongly typed observable behavioral state at step t."""
    step: int
    opp_visible_hands: int
    opp_visible_quadrants: int
    opp_visible_cash: float
    current_prices: Dict[str, float]
    price_ratios: Dict[str, float]
    crop_price_index: float
    livestock_price_index: float
    crop_sell_pressure: float
    livestock_sell_pressure: float
    inferred_behavior_class: str

    def to_feature_vector(self) -> np.ndarray:
        feats = [
            float(self.step) / 720.0,
            float(self.opp_visible_hands),
            float(self.opp_visible_quadrants),
            float(self.opp_visible_cash) / 100000.0,
            self.crop_price_index,
            self.livestock_price_index,
            self.crop_sell_pressure,
            self.livestock_sell_pressure,
        ]
        for c in COMMODITIES:
            feats.append(self.price_ratios.get(c, 1.0))
        return np.array(feats, dtype=np.float32)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "opp_visible_hands": self.opp_visible_hands,
            "opp_visible_quadrants": self.opp_visible_quadrants,
            "opp_visible_cash": self.opp_visible_cash,
            "crop_price_index": self.crop_price_index,
            "livestock_price_index": self.livestock_price_index,
            "crop_sell_pressure": self.crop_sell_pressure,
            "livestock_sell_pressure": self.livestock_sell_pressure,
            "inferred_behavior_class": self.inferred_behavior_class,
            "price_ratios": self.price_ratios,
        }


class OpponentBehaviorTracker:
    """Stateful observable tracker maintaining sliding window history."""

    def __init__(self, history_len: int = 12):
        self.history_len = history_len
        self.price_history: List[Dict[str, float]] = []
        self.step_history: List[int] = []

    def reset(self):
        self.price_history.clear()
        self.step_history.clear()

    def update(self, observation: Dict[str, Any]) -> OpponentBehaviorSnapshot:
        """Processes current observation and returns an OpponentBehaviorSnapshot."""
        # Check against forbidden keys
        for k in observation.keys():
            if k.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"LEAKAGE DETECTED: Observation contains forbidden key {k}")

        step = int(observation.get("step", 0) or 0)
        player = int(observation.get("player", 0) or 0)
        opp_player = 1 - player

        farms = observation.get("farms", []) or []
        opp_farm = farms[opp_player] if len(farms) > opp_player else {}

        opp_hands = len(opp_farm.get("hands", []) or [])
        opp_quads = len(opp_farm.get("unlocked_quadrants", []) or [1])
        opp_cash = float(opp_farm.get("money", 0.0) or 0.0)

        mkt = observation.get("market", {}) or {}
        raw_prices = mkt.get("prices", {}) or {}
        prices = {c: float(raw_prices.get(c, BASE_PRICES[c]) or BASE_PRICES[c]) for c in COMMODITIES}

        self.price_history.append(prices)
        self.step_history.append(step)
        if len(self.price_history) > self.history_len:
            self.price_history.pop(0)
            self.step_history.pop(0)

        # Price ratios relative to baseline
        price_ratios = {c: prices[c] / BASE_PRICES[c] for c in COMMODITIES}

        # Basket indices
        crop_items = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
        livestock_items = ["EGG", "MILK", "WOOL"]

        crop_index = float(np.mean([price_ratios[c] for c in crop_items]))
        livestock_index = float(np.mean([price_ratios[c] for c in livestock_items]))

        # Price delta over recent window (negative delta = sell pressure)
        if len(self.price_history) >= 4:
            oldest = self.price_history[0]
            crop_deltas = [prices[c] - oldest[c] for c in crop_items]
            live_deltas = [prices[c] - oldest[c] for c in livestock_items]
            crop_sell_pressure = float(-np.mean(crop_deltas))
            livestock_sell_pressure = float(-np.mean(live_deltas))
        else:
            crop_sell_pressure = 0.0
            livestock_sell_pressure = 0.0

        # Behavioral Classification (OBSERVABLE BEHAVIOR ONLY, NEVER AGENT IDENTITY)
        if crop_sell_pressure > 5.0 and crop_index < 0.85:
            inferred_class = "HIGH_CROP_SATURATION"
        elif livestock_sell_pressure > 8.0 and livestock_index < 0.85:
            inferred_class = "HIGH_LIVESTOCK_SATURATION"
        elif crop_sell_pressure > 8.0 and livestock_sell_pressure > 8.0:
            inferred_class = "HIGH_AGGRESSION_DUMP"
        elif crop_index > 1.15 and livestock_index > 1.15:
            inferred_class = "SCARCITY_HIGH_PRICE"
        else:
            inferred_class = "BALANCED_REGIME"

        return OpponentBehaviorSnapshot(
            step=step,
            opp_visible_hands=opp_hands,
            opp_visible_quadrants=opp_quads,
            opp_visible_cash=opp_cash,
            current_prices=prices,
            price_ratios=price_ratios,
            crop_price_index=crop_index,
            livestock_price_index=livestock_index,
            crop_sell_pressure=crop_sell_pressure,
            livestock_sell_pressure=livestock_sell_pressure,
            inferred_behavior_class=inferred_class,
        )
