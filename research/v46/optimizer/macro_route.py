# SPDX-License-Identifier: MIT
"""V46 Phase 3: Macroeconomic Route Parameterization & Deterministic Executor.

Parameterizes full-game agricultural economic trajectories into structured macro vectors:
- Land expansion schedule
- Labor hire curve (daily hands and ceiling)
- Livestock allocation (Cows, Sheep, Geese, buy days, structure timing)
- Crop allocation & rotation (Wheat, Strawberry, Melon, Carrot, Tomato)
- Fertilizer, watering, care, and feeding policies
- Investment payback cutoff (Step 520+ amortization protection)
- Order-book liquidation schedule & Town demand reaction
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CROPS = {
    "WHEAT": {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 4},
    "CARROT": {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False, "base_yield": 3},
    "TOMATO": {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True, "base_yield": 4},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True, "base_yield": 4},
    "MELON": {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 6},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW": {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
LAND_COSTS = [1000, 2000, 4000]


@dataclass
class MacroRouteConfig:
    route_id: str
    name: str
    description: str
    # Opening capital management
    opening_wash: Tuple[int, int] = (25, 25)
    # Land expansion timing (days where land purchase is authorized if cash allows)
    land_purchase_days: List[int] = field(default_factory=lambda: [0, 8, 16])
    max_land_quadrants: int = 4
    # Labor schedule
    max_hands: int = 20
    daily_hire_ceiling: int = 2
    # Livestock strategy
    target_cows: int = 6
    target_sheep: int = 3
    target_geese: int = 0
    cow_buy_day: int = 2
    sheep_buy_day: int = 4
    # Crop strategy
    primary_crop: str = "WHEAT"
    primary_crop_count: int = 16
    secondary_crop: str = "STRAWBERRY"
    secondary_crop_count: int = 8
    # Care & Maintenance
    care_policy: bool = True
    feed_policy: bool = True
    fertilize_policy: bool = True
    watering_policy: bool = True
    # Amortization & Payback Cutoff
    payback_cutoff_step: int = 520
    # Liquidation schedule: step -> fraction of shed stock to sell
    liquidation_schedule: Dict[int, float] = field(default_factory=lambda: {
        693: 0.5,
        704: 0.5,
        716: 1.0
    })
    # Town demand adaptation
    town_demand_react: bool = True


def get_unlocked_shed_tiles(tiles):
    half = len(tiles) // 2
    candidates = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_next_step(start, target, tiles):
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target
    moves = []
    if tx > sx and tiles[sy][sx + 1] != "LOCKED":
        moves.append("EAST")
    if tx < sx and tiles[sy][sx - 1] != "LOCKED":
        moves.append("WEST")
    if ty > sy and tiles[sy + 1][sx] != "LOCKED":
        moves.append("SOUTH")
    if ty < sy and tiles[sy - 1][sx] != "LOCKED":
        moves.append("NORTH")
    if not moves:
        for m, (dx, dy) in [("EAST", (1, 0)), ("WEST", (-1, 0)), ("SOUTH", (0, 1)), ("NORTH", (0, -1))]:
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles) and tiles[ny][nx] != "LOCKED":
                moves.append(m)
    return moves[0] if moves else "PASS"


class MacroRouteExecutor:
    """Stateful deterministic controller executing a parameterized MacroRouteConfig."""

    def __init__(self, config: MacroRouteConfig):
        self.cfg = config
        self.reset()

    def reset(self):
        self.step_history = []
        self.hires_by_day = {}

    def act(self, obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            player = obs.get("player", 0)
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)

            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0) or 0.0)
            farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0) or 0)
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]) or ["NW"])
            tiles = farm.get("tiles", [[None] * 10 for _ in range(10)])

            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            seeds = dict(private.get("seeds", {}) or {})
            inventories = [dict(inv or {}) for inv in private.get("inventories", [{}])]

            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}) or {})

            # 1. Step 0 Opening Wash
            if step == 0:
                wash_buy, wash_sell = self.cfg.opening_wash
                orders = []
                if wash_buy > 0 and wash_sell > 0:
                    orders = [
                        ["BUY_PRODUCT", "WHEAT", wash_buy],
                        ["SELL", "WHEAT", wash_sell]
                    ]
                return {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": orders
                }

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            goose_count = 0
            pasture_count = 0
            empty_pastures = []
            coop_count = 0
            empty_coops = []
            crop_counts = {c: 0 for c in CROPS}
            unfed_animal_tiles = []

            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    pos = (x, y)
                    if t is None:
                        empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": pos, "weight": 95})
                        elif kind == "COOP":
                            coop_count += 1
                            if "animal" in t and t.get("animal"):
                                goose_count += 1
                                if self.cfg.feed_policy and not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 90})
                                    unfed_animal_tiles.append(pos)
                                if self.cfg.care_policy and not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 75})
                                if self.cfg.fertilize_policy and t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 85})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_coops.append(pos)
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a_type = t.get("animal")
                                if a_type == "COW":
                                    cow_count += 1
                                elif a_type == "SHEEP":
                                    sheep_count += 1
                                if self.cfg.feed_policy and not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                    unfed_animal_tiles.append(pos)
                                if self.cfg.care_policy and not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if self.cfg.fertilize_policy and t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop in crop_counts:
                                crop_counts[crop] += 1
                            if self.cfg.watering_policy and not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 88})
                            if t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            # 2. Market Orders & Macro Resource Allocations
            # Pre-terminal payback cutoff (step >= 520 suppresses non-amortizing outlays)
            if step < self.cfg.payback_cutoff_step:
                # Land Expansion
                if day in self.cfg.land_purchase_days and len(unlocked_quads) < self.cfg.max_land_quadrants:
                    next_land_idx = len(unlocked_quads) - 1
                    if 0 <= next_land_idx < len(LAND_COSTS):
                        land_cost = LAND_COSTS[next_land_idx]
                        if money >= land_cost + 200:
                            orders.append(["BUY_LAND"])
                            money -= land_cost

                # Labor Hires
                total_hands_now = len(hands)
                if total_hands_now < self.cfg.max_hands and hires_today < self.cfg.daily_hire_ceiling and hour == 0:
                    orders.append(["HIRE"])

                # Livestock Acquisition
                if day >= self.cfg.cow_buy_day and cow_count + len(empty_pastures) < self.cfg.target_cows:
                    if empty_pastures:
                        if money >= ANIMALS["COW"]["cost"]:
                            orders.append(["BUY_ANIMAL", "COW", 1])
                            money -= ANIMALS["COW"]["cost"]
                    elif empty_tiles and money >= ANIMALS["COW"]["cost"] + 150:
                        # Will build pasture
                        pass

                if day >= self.cfg.sheep_buy_day and sheep_count + len(empty_pastures) < self.cfg.target_sheep:
                    if empty_pastures:
                        if money >= ANIMALS["SHEEP"]["cost"]:
                            orders.append(["BUY_ANIMAL", "SHEEP", 1])
                            money -= ANIMALS["SHEEP"]["cost"]

                # Seed Purchases
                p_crop = self.cfg.primary_crop
                if crop_counts.get(p_crop, 0) < self.cfg.primary_crop_count and seeds.get(p_crop, 0) < 5:
                    scost = CROPS[p_crop]["seed"] * 5
                    if money >= scost + 50:
                        orders.append(["BUY_SEED", p_crop, 5])
                        money -= scost

                s_crop = self.cfg.secondary_crop
                if crop_counts.get(s_crop, 0) < self.cfg.secondary_crop_count and seeds.get(s_crop, 0) < 4:
                    scost = CROPS[s_crop]["seed"] * 4
                    if money >= scost + 50:
                        orders.append(["BUY_SEED", s_crop, 4])
                        money -= scost

                # Animal Feed Purchases
                if (cow_count + sheep_count + goose_count) > 0:
                    wheat_needed = (cow_count + sheep_count + goose_count) * 2
                    wheat_in_shed = shed.get("WHEAT", 0)
                    if wheat_in_shed < wheat_needed and money >= 100:
                        buy_qty = min(20, wheat_needed - wheat_in_shed)
                        if buy_qty > 0:
                            orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])

            # 3. Liquidation Schedule (Staggered pre-emption & final flush)
            if step in self.cfg.liquidation_schedule:
                frac = self.cfg.liquidation_schedule[step]
                marketable = ("STRAWBERRY", "MILK", "WOOL", "MELON", "EGG")
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty > 0 and len(orders) < 10:
                        sell_qty = max(1, int(qty * frac)) if frac < 1.0 else qty
                        orders.append(["SELL", item, sell_qty])

            # 4. Units Chore Dispatch (Farmer and Hands)
            actors = [farmer_pos] + hands
            assigned_actions = []

            unlocked_shed = get_unlocked_shed_tiles(tiles)
            primary_shed = unlocked_shed[0] if unlocked_shed else (4, 4)

            for idx, actor_pos in enumerate(actors):
                inv = inventories[idx] if idx < len(inventories) else {}
                held_items = sum(inv.values())

                # A. Drop inventory if full or near shed
                if held_items > 0:
                    if manhattan(actor_pos, primary_shed) <= 1:
                        assigned_actions.append(["DROP"])
                        continue
                    elif held_items >= 5:
                        mv = get_next_step(actor_pos, primary_shed, tiles)
                        assigned_actions.append([mv])
                        continue

                # B. Build pastures if livestock needed
                needed_pastures = (self.cfg.target_cows + self.cfg.target_sheep) - (pasture_count)
                if needed_pastures > 0 and empty_tiles and idx == 0 and step < self.cfg.payback_cutoff_step:
                    target_pos = empty_tiles[0]
                    if actor_pos == target_pos:
                        assigned_actions.append(["BUILD_PASTURE"])
                        empty_tiles.pop(0)
                        pasture_count += 1
                        continue
                    else:
                        mv = get_next_step(actor_pos, target_pos, tiles)
                        assigned_actions.append([mv])
                        continue

                # C. Plant crops if seeds in hand/pocket
                p_crop = self.cfg.primary_crop
                if empty_tiles and seeds.get(p_crop, 0) > 0 and crop_counts.get(p_crop, 0) < self.cfg.primary_crop_count:
                    target_pos = empty_tiles[0]
                    if actor_pos == target_pos:
                        assigned_actions.append(["PLANT", p_crop])
                        empty_tiles.pop(0)
                        crop_counts[p_crop] += 1
                        continue
                    else:
                        mv = get_next_step(actor_pos, target_pos, tiles)
                        assigned_actions.append([mv])
                        continue

                # D. Dispatch highest-weight chores
                if chores:
                    # Sort chores by weight and proximity
                    chores.sort(key=lambda c: (c["weight"], -manhattan(actor_pos, c["pos"])), reverse=True)
                    target_chore = chores[0]
                    c_pos = target_chore["pos"]
                    c_type = target_chore["type"]

                    if actor_pos == c_pos:
                        if c_type == "HARVEST":
                            assigned_actions.append(["HARVEST"])
                        elif c_type == "WATER":
                            assigned_actions.append(["WATER"])
                        elif c_type == "CARE":
                            assigned_actions.append(["CARE"])
                        elif c_type == "FEED":
                            assigned_actions.append(["FEED"])
                        elif c_type == "COLLECT_FERTILIZER":
                            assigned_actions.append(["COLLECT_FERTILIZER"])
                        elif c_type == "DIG":
                            assigned_actions.append(["DIG"])
                        else:
                            assigned_actions.append(["PASS"])
                        chores.pop(0)
                        continue
                    else:
                        mv = get_next_step(actor_pos, c_pos, tiles)
                        assigned_actions.append([mv])
                        continue

                # Default fallback
                assigned_actions.append(["PASS"])

            farmer_act = assigned_actions[0] if assigned_actions else ["PASS"]
            hands_act = assigned_actions[1:] if len(assigned_actions) > 1 else []

            return {
                "farmer": farmer_act,
                "hands": hands_act,
                "market": orders[:10]
            }

        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}
