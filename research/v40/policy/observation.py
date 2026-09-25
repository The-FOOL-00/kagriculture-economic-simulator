# SPDX-License-Identifier: MIT
"""Kagriculture V40 Strategic Observation Space Encoder.

Builds a clean, normalized, multi-group macroeconomic observation vector:
1. Economy (capital, runway, liquidity, net worth, velocity)
2. Inventory (commodity quantities, liquidation value, time sensitivity)
3. Market (spot prices, price deltas, momentum, market depth)
4. Production (crop stages, animal censuses, labor utilization, land)
5. Temporal (step, day, hour, phase, distance to cycles)
6. Strategic History (previous macro action, rolling trajectories)

Strict Zero-Leakage Compliance:
- Strictly observable information only
- Zero access to opponent private inventories
- Zero access to future prices, random seeds, or opponent ID strings
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Official game constants
COMMODITIES = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("COW", "SHEEP", "GOOSE")
STARTING_MONEY = 3000.0
SHED_CAPACITY = 100.0
TOTAL_STEPS = 720.0
WAGE_PER_HAND_PER_DAY = 10.0

# Strategic action count (matches V40 macro action space: 16 discrete actions)
NUM_STRATEGIC_ACTIONS = 16


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
    """Tracks state trajectory over recent steps for temporal momentum features."""
    prev_prices: Dict[str, float] = field(default_factory=dict)
    price_momentums: Dict[str, float] = field(default_factory=dict)
    recent_cash: List[float] = field(default_factory=list)
    recent_actions: List[int] = field(default_factory=list)
    recent_sales_volume: float = 0.0
    recent_expansion_step: int = -100
    recent_hire_step: int = -100


class V40ObservationEncoder:
    """Extracts, normalizes, and vectorizes observation into a fixed-length feature tensor."""

    def __init__(self, include_history: bool = True):
        self.include_history = include_history
        self.history = ObservationHistory()

    def reset(self):
        self.history = ObservationHistory()

    def encode(
        self,
        obs: Dict[str, Any],
        player: int = 0,
        prev_macro_action: Optional[int] = None
    ) -> np.ndarray:
        """Translates raw observation into normalized numpy float32 feature vector."""
        step = int(_get(obs, "step", 0) or 0)
        day = int(_get(obs, "day", step // 24) or 0)
        hour = int(_get(obs, "hour", step % 24) or 0)

        farms = list(_get(obs, "farms", []) or [])
        my_farm = farms[player] if farms and player < len(farms) else {}
        opp_farm = farms[1 - player] if farms and (1 - player) < len(farms) else {}

        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        seeds = dict(_get(private, "seeds", {}) or {})
        inventories = list(_get(private, "inventories", []) or [])

        market = _get(obs, "market", {}) or {}
        prices_raw = dict(_get(market, "prices", {}) or {})
        market_inv = dict(_get(market, "inventory", {}) or {})

        # Extract current prices
        current_prices = {item: _safe_float(prices_raw.get(item, 20.0)) for item in COMMODITIES}

        # -------------------------------------------------------------
        # 1. ECONOMY FEATURES (12 dims)
        # -------------------------------------------------------------
        cash = _safe_float(_get(my_farm, "money", 0.0))
        opp_cash = _safe_float(_get(opp_farm, "money", 0.0))

        norm_cash = np.clip(cash / 100000.0, 0.0, 2.0)  # ~$100k scale
        cash_ratio_to_start = np.clip(cash / STARTING_MONEY, 0.0, 40.0) / 40.0
        relative_cash_lead = np.clip((cash - opp_cash) / 20000.0, -2.0, 2.0)

        # Inventory valuation
        total_shed_units = sum(shed.get(item, 0) for item in COMMODITIES)
        shed_liquidation_value = sum(shed.get(item, 0) * current_prices[item] for item in COMMODITIES)
        norm_shed_val = np.clip(shed_liquidation_value / 50000.0, 0.0, 2.0)

        # Liquid inventory value (high-value market goods)
        liquid_val = sum(shed.get(item, 0) * current_prices[item] for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"))
        norm_liquid_val = np.clip(liquid_val / 30000.0, 0.0, 2.0)

        # Net worth
        net_worth = cash + shed_liquidation_value
        norm_net_worth = np.clip(net_worth / 120000.0, 0.0, 2.0)

        # Cash velocity / delta
        recent_cash = self.history.recent_cash
        recent_cash.append(cash)
        if len(recent_cash) > 5:
            recent_cash.pop(0)
        cash_delta_short = (cash - recent_cash[0]) if len(recent_cash) > 1 else 0.0
        norm_cash_delta = np.clip(cash_delta_short / 5000.0, -2.0, 2.0)

        # Labor wage liability
        hands_count = len(list(_get(my_farm, "hands", []) or []))
        total_workers = 1 + hands_count
        daily_wages = hands_count * WAGE_PER_HAND_PER_DAY
        days_wage_runway = (cash / daily_wages) if daily_wages > 0 else 100.0
        norm_wage_runway = np.clip(days_wage_runway / 30.0, 0.0, 1.0)
        solvency_risk = 1.0 if days_wage_runway < 2.0 else 0.0

        economy_features = [
            norm_cash,
            cash_ratio_to_start,
            relative_cash_lead,
            norm_shed_val,
            norm_liquid_val,
            norm_net_worth,
            norm_cash_delta,
            norm_wage_runway,
            solvency_risk,
            np.clip(daily_wages / 200.0, 0.0, 1.0),
            np.clip(cash / 500.0, 0.0, 1.0),  # Liquidity safety floor indicator ($500)
            np.clip(cash / 100.0, 0.0, 1.0),  # Critical distress indicator ($100)
        ]

        # -------------------------------------------------------------
        # 2. INVENTORY FEATURES (9 commodities x 3 metrics = 27 dims)
        # -------------------------------------------------------------
        inventory_features = []
        for item in COMMODITIES:
            qty_shed = float(shed.get(item, 0))
            norm_qty_shed = np.clip(qty_shed / SHED_CAPACITY, 0.0, 1.0)

            # Quantity in hands
            qty_in_hands = sum(float(_get(inv, item, 0)) for inv in inventories)
            norm_qty_hands = np.clip(qty_in_hands / 20.0, 0.0, 1.0)

            # Item value contribution
            item_val = qty_shed * current_prices[item]
            norm_item_val = np.clip(item_val / 10000.0, 0.0, 1.0)

            inventory_features.extend([norm_qty_shed, norm_qty_hands, norm_item_val])

        # -------------------------------------------------------------
        # 3. MARKET FEATURES (9 commodities x 3 metrics = 27 dims)
        # -------------------------------------------------------------
        market_features = []
        for item in COMMODITIES:
            price = current_prices[item]
            norm_price = np.clip(price / 100.0, 0.0, 1.5)

            # Price delta from previous step
            prev_price = self.history.prev_prices.get(item, price)
            price_delta = price - prev_price
            norm_price_delta = np.clip(price_delta / 10.0, -1.0, 1.0)

            # Price momentum
            prev_mom = self.history.price_momentums.get(item, 0.0)
            cur_mom = 0.8 * prev_mom + 0.2 * norm_price_delta
            self.history.price_momentums[item] = cur_mom

            market_features.extend([norm_price, norm_price_delta, cur_mom])

        # Update price history
        self.history.prev_prices = dict(current_prices)

        # -------------------------------------------------------------
        # 4. PRODUCTION & PHYSICAL CENSUS FEATURES (18 dims)
        # -------------------------------------------------------------
        tiles = list(_get(my_farm, "tiles", []) or [])
        empty_tiles = 0
        weed_tiles = 0
        locked_tiles = 0
        planted_crops = {c: 0 for c in CROPS}
        watered_today = 0
        unwatered_crops = 0
        harvestable_crops = 0
        pasture_count = 0
        coop_count = 0
        animal_counts = {a: 0 for a in ANIMALS}
        unfed_animals = 0

        for row in tiles:
            for tile in (row or []):
                if tile is None:
                    empty_tiles += 1
                elif tile == "LOCKED":
                    locked_tiles += 1
                elif isinstance(tile, dict):
                    kind = tile.get("kind")
                    if kind == "WEED":
                        weed_tiles += 1
                    elif kind == "PLANT":
                        c = tile.get("crop")
                        if c in planted_crops:
                            planted_crops[c] += 1
                        if tile.get("watered_today"):
                            watered_today += 1
                        else:
                            unwatered_crops += 1
                        if _safe_float(tile.get("yield_units", 0)) > 0:
                            harvestable_crops += 1
                    elif kind == "PASTURE":
                        pasture_count += 1
                        a = tile.get("animal")
                        if a in animal_counts:
                            animal_counts[a] += 1
                            if not tile.get("fed_today"):
                                unfed_animals += 1
                    elif kind == "COOP":
                        coop_count += 1
                        a = tile.get("animal")
                        if a in animal_counts:
                            animal_counts[a] += 1
                            if not tile.get("fed_today"):
                                unfed_animals += 1

        unlocked_quads = len(list(_get(my_farm, "unlocked_quadrants", []) or [0]))
        total_crops = sum(planted_crops.values())

        production_features = [
            np.clip(total_workers / 15.0, 0.0, 1.0),
            np.clip(unlocked_quads / 4.0, 0.0, 1.0),
            np.clip(empty_tiles / 100.0, 0.0, 1.0),
            np.clip(weed_tiles / 20.0, 0.0, 1.0),
            np.clip(locked_tiles / 75.0, 0.0, 1.0),
            np.clip(total_crops / 50.0, 0.0, 1.0),
            np.clip(planted_crops["WHEAT"] / 25.0, 0.0, 1.0),
            np.clip(planted_crops["MELON"] / 25.0, 0.0, 1.0),
            np.clip(planted_crops["CARROT"] / 25.0, 0.0, 1.0),
            np.clip(planted_crops["STRAWBERRY"] / 25.0, 0.0, 1.0),
            np.clip(unwatered_crops / max(1, total_crops), 0.0, 1.0),
            np.clip(harvestable_crops / 25.0, 0.0, 1.0),
            np.clip(animal_counts["COW"] / 10.0, 0.0, 1.0),
            np.clip(animal_counts["SHEEP"] / 10.0, 0.0, 1.0),
            np.clip(animal_counts["GOOSE"] / 10.0, 0.0, 1.0),
            np.clip(unfed_animals / max(1, sum(animal_counts.values())), 0.0, 1.0),
            np.clip(pasture_count / 15.0, 0.0, 1.0),
            np.clip(coop_count / 10.0, 0.0, 1.0),
        ]

        # -------------------------------------------------------------
        # 5. TEMPORAL & CYCLE FEATURES (10 dims)
        # -------------------------------------------------------------
        norm_step = float(step) / TOTAL_STEPS
        norm_time_remaining = (TOTAL_STEPS - float(step)) / TOTAL_STEPS
        norm_day = float(day) / 30.0
        norm_hour = float(hour) / 24.0

        # Game Phase indicator
        is_phase_early = 1.0 if step < 144 else 0.0     # Days 0-5
        is_phase_mid = 1.0 if 144 <= step < 504 else 0.0 # Days 6-20
        is_phase_late = 1.0 if 504 <= step < 672 else 0.0 # Days 21-27
        is_phase_terminal = 1.0 if step >= 672 else 0.0 # Days 28-29

        # Periodic cycle countdowns
        dist_to_midnight = float((24 - hour) % 24) / 24.0
        dist_to_town_cycle = float((4 - (step % 4)) % 4) / 4.0

        temporal_features = [
            norm_step,
            norm_time_remaining,
            norm_day,
            norm_hour,
            is_phase_early,
            is_phase_mid,
            is_phase_late,
            is_phase_terminal,
            dist_to_midnight,
            dist_to_town_cycle,
        ]

        # -------------------------------------------------------------
        # 6. STRATEGIC HISTORY & ACTION FEEDBACK (18 dims)
        # -------------------------------------------------------------
        action_one_hot = [0.0] * NUM_STRATEGIC_ACTIONS
        if prev_macro_action is not None and 0 <= prev_macro_action < NUM_STRATEGIC_ACTIONS:
            action_one_hot[prev_macro_action] = 1.0

        recent_expansion = 1.0 if (step - self.history.recent_expansion_step) < 24 else 0.0
        recent_hire = 1.0 if (step - self.history.recent_hire_step) < 24 else 0.0

        history_features = action_one_hot + [recent_expansion, recent_hire]

        # -------------------------------------------------------------
        # COMPOSE COMPLETE OBSERVATION VECTOR
        # Total Dimensions: 12 + 27 + 27 + 18 + 10 + 18 = 112 dims
        # -------------------------------------------------------------
        vector = np.array(
            economy_features +
            inventory_features +
            market_features +
            production_features +
            temporal_features +
            history_features,
            dtype=np.float32
        )

        # Guarantee numerical sanitization
        vector = np.nan_to_num(vector, nan=0.0, posinf=1.0, neginf=-1.0)
        return vector


OBSERVATION_DIM = 112
