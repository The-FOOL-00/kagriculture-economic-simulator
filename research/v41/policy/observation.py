# SPDX-License-Identifier: MIT
"""Kagriculture V41 Strategic Observation Space Encoder.

Builds a clean, normalized, zero-leakage macroeconomic observation vector:
1. Economy: capital, runway, liquidity, net worth, velocity (8 dims)
2. Inventory: commodity quantities, liquidation value, time sensitivity (25 dims)
3. Market: spot prices, price momentum, spreads (30 dims)
4. Production: crop stages, animal counts, labor utilization, land (24 dims)
5. Temporal: step, day, hour, phase, distance to terminal (5 dims)
6. Strategic Intervention History: one-hot previous safe intervention (11 dims)
Total: 103 normalized dimensions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from research.v41.executor.safe_executor import NUM_INTERVENTIONS, INTERVENTION_NAMES

COMMODITIES = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("COW", "SHEEP", "GOOSE")
STARTING_MONEY = 3000.0
SHED_CAPACITY = 100.0
TOTAL_STEPS = 720.0

OBSERVATION_DIM = 103


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return default


@dataclass
class ObservationHistory:
    prev_prices: Dict[str, float] = field(default_factory=dict)
    price_momentums: Dict[str, float] = field(default_factory=dict)
    recent_cash: List[float] = field(default_factory=list)
    recent_interventions: List[int] = field(default_factory=list)


class V41ObservationEncoder:
    """Zero-leakage observation encoder for V41 strategic policy."""

    def __init__(self):
        self.history = ObservationHistory()

    def reset(self):
        self.history = ObservationHistory()

    def encode(
        self,
        obs: Dict[str, Any],
        player: int = 0,
        prev_intervention: Optional[int] = None
    ) -> np.ndarray:
        step = int(_get(obs, "step", 0) or 0)
        day = int(_get(obs, "day", step // 24) or 0)
        hour = int(_get(obs, "hour", step % 24) or 0)

        farms = list(_get(obs, "farms", []) or [])
        my_farm = farms[player] if farms and player < len(farms) else {}

        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        seeds = dict(_get(private, "seeds", {}) or {})
        inventories = list(_get(private, "inventories", []) or [])

        market = _get(obs, "market", {}) or {}
        prices_raw = dict(_get(market, "prices", {}) or {})

        current_prices = {item: _safe_float(prices_raw.get(item, 20.0)) for item in COMMODITIES}

        # Update price momentum
        momentums = {}
        for item in COMMODITIES:
            prev = self.history.prev_prices.get(item, current_prices[item])
            momentums[item] = (current_prices[item] - prev) / max(1.0, prev)
        self.history.prev_prices = dict(current_prices)
        self.history.price_momentums = dict(momentums)

        cash = _safe_float(_get(my_farm, "money", 0.0))
        self.history.recent_cash.append(cash)
        if len(self.history.recent_cash) > 10:
            self.history.recent_cash.pop(0)

        if prev_intervention is not None:
            self.history.recent_interventions.append(prev_intervention)
            if len(self.history.recent_interventions) > 10:
                self.history.recent_interventions.pop(0)

        # 1. Economy features (8 dims)
        liq_value = sum(shed.get(item, 0) * current_prices[item] for item in COMMODITIES)
        net_worth = cash + liq_value
        cash_ratio = cash / max(1.0, net_worth)
        cash_delta_recent = (cash - self.history.recent_cash[0]) / 5000.0 if len(self.history.recent_cash) > 1 else 0.0

        economy_features = [
            np.clip(cash / 50000.0, 0.0, 5.0),
            np.clip(net_worth / 100000.0, 0.0, 5.0),
            np.clip(liq_value / 25000.0, 0.0, 5.0),
            np.clip(cash_ratio, 0.0, 1.0),
            np.clip(cash_delta_recent, -2.0, 2.0),
            1.0 if cash < 500.0 else 0.0,
            1.0 if cash >= 12000.0 else 0.0,
            1.0 if step >= 680 else 0.0,
        ]

        # 2. Inventory features (25 dims)
        total_shed_count = sum(shed.get(item, 0) for item in COMMODITIES)
        shed_utilization = total_shed_count / SHED_CAPACITY
        inv_features = [
            np.clip(shed_utilization, 0.0, 1.5),
            1.0 if total_shed_count >= 85 else 0.0,
        ]
        # Quantities in shed (9 dims)
        for item in COMMODITIES:
            inv_features.append(np.clip(shed.get(item, 0) / 50.0, 0.0, 2.0))
        # Quantities in hands (9 dims)
        for item in COMMODITIES:
            in_hand = sum(max(0, int(dict(i or {}).get(item, 0))) for i in inventories)
            inv_features.append(np.clip(in_hand / 10.0, 0.0, 2.0))
        # Seed counts (5 dims)
        for crop in CROPS:
            inv_features.append(np.clip(seeds.get(crop, 0) / 20.0, 0.0, 2.0))

        # 3. Market features (30 dims)
        mkt_features = []
        # Normalized prices (9 dims)
        for item in COMMODITIES:
            mkt_features.append(np.clip(current_prices[item] / 60.0, 0.0, 2.0))
        # Momentums (9 dims)
        for item in COMMODITIES:
            mkt_features.append(np.clip(momentums[item], -1.0, 1.0))
        # High spot indicators (6 dims)
        for item in ("MILK", "WOOL", "STRAWBERRY", "MELON", "CARROT", "TOMATO"):
            mkt_features.append(1.0 if current_prices[item] >= 30.0 else 0.0)
        # Depressed spot indicators (6 dims)
        for item in ("MILK", "WOOL", "STRAWBERRY", "MELON", "CARROT", "TOMATO"):
            mkt_features.append(1.0 if current_prices[item] < 18.0 else 0.0)

        # 4. Production & Labor features (24 dims)
        quads = len(list(_get(my_farm, "unlocked_quadrants", [0]) or [0]))
        hands = list(_get(my_farm, "hands", []) or [])
        worker_count = 1 + len(hands)

        tiles = list(_get(my_farm, "tiles", []) or [])
        weed_count = 0
        crop_count = 0
        animal_count = 0
        for row in tiles:
            for tile in (row or []):
                if isinstance(tile, dict):
                    kind = tile.get("kind")
                    if kind == "WEED":
                        weed_count += 1
                    elif kind == "PLANT":
                        crop_count += 1
                    elif tile.get("animal"):
                        animal_count += 1

        prod_features = [
            quads / 4.0,
            worker_count / 14.0,
            np.clip(weed_count / 20.0, 0.0, 1.0),
            np.clip(crop_count / 30.0, 0.0, 2.0),
            np.clip(animal_count / 10.0, 0.0, 2.0),
            1.0 if quads < 4 else 0.0,
            1.0 if worker_count >= 8 else 0.0,
            1.0 if weed_count > 0 else 0.0,
        ]
        # Pad to 24 dims
        prod_features.extend([0.0] * (24 - len(prod_features)))

        # 5. Temporal features (5 dims)
        time_rem = max(0.0, (TOTAL_STEPS - step) / TOTAL_STEPS)
        temporal_features = [
            step / TOTAL_STEPS,
            time_rem,
            day / 30.0,
            hour / 24.0,
            1.0 if step >= 690 else 0.0,
        ]

        # 6. Strategic Intervention History (11 dims)
        hist_one_hot = np.zeros(NUM_INTERVENTIONS, dtype=np.float32)
        last_int = self.history.recent_interventions[-1] if self.history.recent_interventions else 0
        if 0 <= last_int < NUM_INTERVENTIONS:
            hist_one_hot[last_int] = 1.0

        all_features = (
            economy_features +
            inv_features +
            mkt_features +
            prod_features +
            temporal_features +
            hist_one_hot.tolist()
        )

        return np.array(all_features, dtype=np.float32)
