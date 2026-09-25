# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Deterministic Opponent & Regime Detector.

Extracts interpretable, fully legal regime indicators from game observations.
No hidden simulator state is accessed.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")


@dataclass
class RegimeFeatures:
    step: int
    player: int
    
    # Player financial state
    player_cash: float
    player_worker_count: int
    player_shed_inventory: Dict[str, int]
    
    # Opponent observable state
    opp_cash: float
    opp_cash_delta_recent: float
    opp_worker_count: int
    opp_cows: int
    opp_sheep: int
    opp_crops: Dict[str, int]
    
    # Market observable dynamics
    spot_prices: Dict[str, float]
    price_changes: Dict[str, float]
    market_inventory: Dict[str, int]
    market_inventory_changes: Dict[str, int]
    town_consumption_due_steps: int
    
    # Inferred Opponent Activity
    opp_recent_sales: Dict[str, int]
    opp_is_selling_frequently: bool
    
    # Active Regime Flags
    flags: Dict[str, bool] = field(default_factory=dict)
    primary_regime: str = "NORMAL"


class DeterministicRegimeDetector:
    """Detects economic and adversarial regimes without machine learning."""
    def __init__(self):
        self.prev_obs: Optional[Dict[str, Any]] = None
        self.prev_market_inv: Dict[str, int] = {}
        self.prev_prices: Dict[str, float] = {}
        self.prev_opp_cash: float = 0.0
        self.opp_sales_history: List[Dict[str, int]] = []
        
    def reset(self):
        self.prev_obs = None
        self.prev_market_inv = {}
        self.prev_prices = {}
        self.prev_opp_cash = 0.0
        self.opp_sales_history = []

    def detect(self, observation: Dict[str, Any]) -> RegimeFeatures:
        step = int(observation.get("step", 0) or 0)
        player = int(observation.get("player", 0) or 0)
        opp_player = 1 - player
        
        farms = observation.get("farms", [])
        p_farm = farms[player] if player < len(farms) else {}
        opp_farm = farms[opp_player] if opp_player < len(farms) else {}
        
        p_cash = float(p_farm.get("money", 0.0) or 0.0)
        opp_cash = float(opp_farm.get("money", 0.0) or 0.0)
        
        # Player shed inventory (private)
        private = observation.get("private", {}) or {}
        p_shed = dict(private.get("shed", {}) or {})
        
        # Player & Opponent workers
        p_workers = 1 + len(p_farm.get("hands", []) or [])
        opp_workers = 1 + len(opp_farm.get("hands", []) or [])
        
        # Opponent board inspection (legal observation)
        opp_tiles = opp_farm.get("tiles", []) or []
        opp_cows = 0
        opp_sheep = 0
        opp_crops = {p: 0 for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]}
        
        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    kind = t.get("kind")
                    animal = t.get("animal")
                    crop = t.get("crop")
                    if animal == "COW":
                        opp_cows += 1
                    elif animal == "SHEEP":
                        opp_sheep += 1
                    elif kind == "PLANT" and crop in opp_crops:
                        opp_crops[crop] += 1
                        
        # Market dynamics
        market = observation.get("market", {}) or {}
        prices = {k: float(v) for k, v in (market.get("prices", {}) or {}).items()}
        market_inv = {k: int(v) for k, v in (market.get("inventory", {}) or {}).items()}
        
        price_changes = {}
        market_inv_changes = {}
        opp_detected_sales = {p: 0 for p in PRODUCTS}
        
        if self.prev_market_inv:
            for prod in PRODUCTS:
                curr_inv = market_inv.get(prod, 0)
                prev_inv = self.prev_market_inv.get(prod, 0)
                inv_delta = curr_inv - prev_inv
                market_inv_changes[prod] = inv_delta
                
                # If market inventory increased and it's not a town consumption step (step % 4 == 0 consumes),
                # that inventory increase is caused by market sales!
                # Since we know our own sales, remaining increase is from opponent.
                if inv_delta > 0:
                    opp_detected_sales[prod] = inv_delta
                    
                price_changes[prod] = prices.get(prod, 0.0) - self.prev_prices.get(prod, 0.0)
        else:
            price_changes = {p: 0.0 for p in PRODUCTS}
            market_inv_changes = {p: 0 for p in PRODUCTS}
            
        opp_cash_delta = opp_cash - self.prev_opp_cash if self.prev_opp_cash > 0 else 0.0
        self.opp_sales_history.append(opp_detected_sales)
        if len(self.opp_sales_history) > 24:
            self.opp_sales_history.pop(0)
            
        # Frequency of opponent sales in recent window
        recent_sales_count = sum(1 for s in self.opp_sales_history if any(v > 0 for v in s.values()))
        opp_is_selling_frequently = recent_sales_count >= 4
        
        # Town consumption timing: town consumes supply every 4 steps
        town_consumption_due = 4 - (step % 4) if (step % 4 != 0) else 0
        
        # Compute discrete regime flags
        flags = {}
        flags["OPPONENT_AGGRESSIVE_SELLER"] = opp_is_selling_frequently or any(market_inv_changes.get(p, 0) >= 8 for p in PRODUCTS)
        flags["OPPONENT_HIGH_LIVESTOCK"] = (opp_cows + opp_sheep) >= 4
        flags["OPPONENT_CROP_HEAVY"] = sum(opp_crops.values()) >= 10
        flags["PLAYER_LOW_LIQUIDITY"] = p_cash < 250.0 and step > 10
        flags["PLAYER_SHED_HIGH_OCCUPANCY"] = sum(p_shed.values()) >= 80
        flags["MARKET_OVERSUPPLIED_MELON"] = market_inv.get("MELON", 0) >= 30 or prices.get("MELON", 100) < 120
        flags["MARKET_OVERSUPPLIED_STRAW"] = market_inv.get("STRAWBERRY", 0) >= 50 or prices.get("STRAWBERRY", 100) < 110
        flags["TERMINAL_WINDOW"] = step >= 710
        
        # Primary Regime Classification
        if flags["TERMINAL_WINDOW"]:
            primary = "TERMINAL_WINDOW"
        elif flags["OPPONENT_AGGRESSIVE_SELLER"]:
            primary = "OPPONENT_SELL_PRESSURE"
        elif flags["PLAYER_LOW_LIQUIDITY"]:
            primary = "LOW_LIQUIDITY_STRESS"
        elif flags["OPPONENT_HIGH_LIVESTOCK"]:
            primary = "LIVESTOCK_RACE"
        elif flags["OPPONENT_CROP_HEAVY"]:
            primary = "CROP_COMPETITION"
        else:
            primary = "NORMAL"
            
        # Update trackers
        self.prev_obs = observation
        self.prev_market_inv = market_inv
        self.prev_prices = prices
        self.prev_opp_cash = opp_cash
        
        return RegimeFeatures(
            step=step,
            player=player,
            player_cash=p_cash,
            player_worker_count=p_workers,
            player_shed_inventory=p_shed,
            opp_cash=opp_cash,
            opp_cash_delta_recent=opp_cash_delta,
            opp_worker_count=opp_workers,
            opp_cows=opp_cows,
            opp_sheep=opp_sheep,
            opp_crops=opp_crops,
            spot_prices=prices,
            price_changes=price_changes,
            market_inventory=market_inv,
            market_inventory_changes=market_inv_changes,
            town_consumption_due_steps=town_consumption_due,
            opp_recent_sales=opp_detected_sales,
            opp_is_selling_frequently=opp_is_selling_frequently,
            flags=flags,
            primary_regime=primary
        )
