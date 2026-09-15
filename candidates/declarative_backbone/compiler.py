"""
EXP-A: Declarative Backbone Compiler
====================================
Translates declarative macroeconomic parameters (BackboneParams) into executable
actions per step without replaying any rigid 719-step sequence.

Features:
- Parameter-driven labor scaling, land milestones, livestock & crop targets.
- 4-Pass Worker Dispatch (Stand-on chores, Shed interactions, Spatial routing, Chore bidding).
- Strict plant maturity gating for HARVEST to prevent zero-yield infinite harvest locks.
- Targeted animal delivery and wheat distribution routing.
"""
from __future__ import annotations
import sys
import os

if "__file__" in globals():
    sys.path.insert(0, os.path.dirname(__file__))
try:
    from params import BackboneParams, V54_PRIOR
except ImportError:
    from candidates.declarative_backbone.params import BackboneParams, V54_PRIOR

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

LAND_PRICES = [1000, 2000, 4000]


def _fib_hire_cost(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _manhattan(p1, p2) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _get_shed_tiles(tiles):
    half = len(tiles) // 2
    candidates = [(half - 1, half - 1), (half, half - 1),
                  (half - 1, half), (half, half)]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]


def _get_next_step(start, target, tiles) -> str:
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
        for m, (dx, dy) in [("EAST", (1, 0)), ("WEST", (-1, 0)),
                             ("SOUTH", (0, 1)), ("NORTH", (0, -1))]:
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles) and tiles[ny][nx] != "LOCKED":
                moves.append(m)
    return moves[0] if moves else "PASS"


class DeclarativeBackboneCompiler:
    def __init__(self, params: BackboneParams = None):
        self.p = params if params is not None else V54_PRIOR
        self._land1_done = False
        self._land2_done = False
        self._melon_seeds_bought = 0
        self._straw_seeds_bought = 0
        self._wheat_seeds_bought = 0

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0)
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)

            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0))
            farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0))
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))
            tiles = farm.get("tiles", [[None] * 10 for _ in range(10)])

            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}))
            seeds = dict(private.get("seeds", {}))
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]

            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            goose_count = 0
            pasture_count = 0
            empty_pastures = []
            melon_plants = 0
            wheat_plants = 0
            straw_plants = 0
            unfed_animal_tiles = []

            # ----------------------------------------------------------
            # Farm Tile Scan & Chore Generation
            # ----------------------------------------------------------
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
                        elif kind in ("COOP", "PASTURE"):
                            if kind == "PASTURE":
                                pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a_type = t.get("animal")
                                if a_type == "COW":
                                    cow_count += 1
                                elif a_type == "SHEEP":
                                    sheep_count += 1
                                elif a_type == "GOOSE":
                                    goose_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                    unfed_animal_tiles.append(pos)
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                if kind == "PASTURE":
                                    empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop == "MELON": melon_plants += 1
                            elif crop == "WHEAT": wheat_plants += 1
                            elif crop == "STRAWBERRY": straw_plants += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            # Strict maturity check for HARVEST
                            if crop == "MELON":
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "STRAWBERRY":
                                if age >= 10 and t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # ----------------------------------------------------------
            # 1. Labor Hiring
            # ----------------------------------------------------------
            total_chores_est = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1:
                target_hands = min(self.p.hire_initial_burst, max(2, (total_chores_est + 6) // 8))
            elif len(unlocked_quads) == 2:
                target_hands = min(self.p.max_workers, max(3, (total_chores_est + 8) // 9))
            else:
                target_hands = min(self.p.max_workers, max(4, (total_chores_est + 10) // 10))

            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = _fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10:
                        orders.append(["HIRE"])
                        money -= cost

            # ----------------------------------------------------------
            # 2. Land Expansion
            # ----------------------------------------------------------
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and step >= self.p.land_expansion_1_step and not self._land1_done:
                    if money >= cost + self.p.initial_cash_reserve:
                        orders.append(["BUY_LAND"])
                        money -= cost
                        self._land1_done = True
                elif n_unlocked == 1 and self.p.land_expansion_2_enabled and step >= self.p.land_expansion_2_step and not self._land2_done:
                    if money >= cost + self.p.initial_cash_reserve:
                        orders.append(["BUY_LAND"])
                        money -= cost
                        self._land2_done = True

            spendable = max(0.0, money - float(self.p.initial_cash_reserve))

            # ----------------------------------------------------------
            # 3. Buy Animals
            # ----------------------------------------------------------
            needed_cows = max(0, self.p.cow_target - cow_count - cows_in_transit)
            needed_sheep = max(0, self.p.sheep_target - sheep_count - sheep_in_transit)
            cows_ordered = 0
            sheep_ordered = 0

            if day <= 14:
                cow_threshold = 695
                sheep_threshold = 595
                if needed_cows > 0 and spendable >= cow_threshold and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    cows_ordered += 1
                if needed_sheep > 0 and spendable >= sheep_threshold and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    sheep_ordered += 1

            total_active_animals += cows_ordered + sheep_ordered

            # ----------------------------------------------------------
            # 4. Feed Reserve Management
            # ----------------------------------------------------------
            if self.p.buy_wheat_for_feed:
                feed_target = total_active_animals * (self.p.feed_reserve_days if day < 26 else 0)
                wheat_in_shed = shed.get("WHEAT", 0)
                if wheat_in_shed < feed_target and spendable >= 25 and len(orders) < 10:
                    wheat_price = market_prices.get("WHEAT", 25)
                    deficit = feed_target - wheat_in_shed
                    max_afford = int(spendable // max(1, wheat_price))
                    to_buy = min(deficit, max_afford, 15)
                    if to_buy > 0:
                        orders.append(["BUY_PRODUCT", "WHEAT", to_buy])
                        spendable -= to_buy * wheat_price
                        money -= to_buy * wheat_price

            # ----------------------------------------------------------
            # 5. Seed Purchasing
            # ----------------------------------------------------------
            # Melons early game
            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.p.melon_seed_count and spendable >= 80 and len(orders) < 10:
                needed = self.p.melon_seed_count - (melon_plants + seeds.get("MELON", 0))
                can_buy = min(needed, int(spendable // 80), 8)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy])
                    spendable -= can_buy * 80
                    money -= can_buy * 80

            # Carrots for fast early revenue
            if day >= 2 and day <= 26 and seeds.get("CARROT", 0) < 8 and spendable >= 40 and len(orders) < 10:
                needed = 8 - seeds.get("CARROT", 0)
                can_buy = min(needed, int(spendable // 20), 6)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "CARROT", can_buy])
                    spendable -= can_buy * 20
                    money -= can_buy * 20

            # Strawberry seeds mid-game
            straw_day = self.p.strawberry_start_step // 24
            if day >= straw_day and day <= straw_day + 10 and self._straw_seeds_bought < self.p.strawberry_seed_count and spendable >= 100 and len(orders) < 10:
                needed = self.p.strawberry_seed_count - self._straw_seeds_bought
                can_buy = min(needed, int(spendable // 100), 4)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    spendable -= can_buy * 100
                    money -= can_buy * 100
                    self._straw_seeds_bought += can_buy

            # ----------------------------------------------------------
            # 6. Selling / Market Liquidation
            # ----------------------------------------------------------
            is_sell_step = step % 4 == 0 or step >= self.p.terminal_liquidation_step
            sell_crops = step >= self.p.sell_start_step
            if is_sell_step:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "STRAWBERRY", "FERTILIZER"]:
                    if prod in ("MELON", "CARROT", "STRAWBERRY") and not sell_crops:
                        continue
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.p.sell_batch_size if step < self.p.terminal_liquidation_step else 30)
                        orders.append(["SELL", prod, batch])

            # ----------------------------------------------------------
            # 7. Worker Dispatch (4-Pass Architecture)
            # ----------------------------------------------------------
            unplaced_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            pastures_to_build = max(0, min(self.p.cow_target + self.p.sheep_target - pasture_count, unplaced_animals - len(empty_pastures)))

            worker_pos = [farmer_pos] + hands
            unassigned = list(range(len(worker_pos)))
            actions = [["PASS"] for _ in range(len(worker_pos))]
            assigned_pos = set()

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

            # Pass 1: Stand-on instant chores
            avail_seeds = dict(seeds)
            for w in list(unassigned):
                pos = worker_pos[w]
                x, y = pos
                t = tiles[y][x]
                inv = inventories[w] if w < len(inventories) else {}

                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED":
                        actions[w] = ["DIG"]
                        unassigned.remove(w); assigned_pos.add(pos); continue
                    elif "animal" in t and t.get("animal"):
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            inv["WHEAT"] -= 1
                            unassigned.remove(w); assigned_pos.add(pos)
                            if pos in unfed_animal_tiles: unfed_animal_tiles.remove(pos)
                            continue
                        if t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w); assigned_pos.add(pos); continue
                        if t.get("fertilizer_available", False):
                            actions[w] = ["COLLECT_FERTILIZER"]
                            unassigned.remove(w); assigned_pos.add(pos); continue
                        if not t.get("cared_today", False):
                            actions[w] = ["CARE"]
                            unassigned.remove(w); assigned_pos.add(pos); continue
                    elif kind == "PASTURE" and "animal" not in t:
                        if inv.get("COW", 0) > 0:
                            actions[w] = ["PLACE", "COW"]
                            inv["COW"] -= 1
                            unassigned.remove(w); assigned_pos.add(pos); continue
                        elif inv.get("SHEEP", 0) > 0:
                            actions[w] = ["PLACE", "SHEEP"]
                            inv["SHEEP"] -= 1
                            unassigned.remove(w); assigned_pos.add(pos); continue
                    elif kind == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w); assigned_pos.add(pos); continue
                        if not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w); assigned_pos.add(pos); continue
                elif t is None:
                    if pastures_to_build > 0:
                        actions[w] = ["BUILD_PASTURE"]
                        pastures_to_build -= 1
                        pasture_count += 1
                        empty_pastures.append(pos)
                        unassigned.remove(w); assigned_pos.add(pos); continue
                    elif day <= 26:
                        for sc in ["MELON", "CARROT", "WHEAT", "STRAWBERRY"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w); assigned_pos.add(pos); break

            # Pass 2: Shed interactions (Stand on shed)
            unlocked_sheds = _get_shed_tiles(tiles)
            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if w_p in unlocked_sheds:
                    if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "COW", 1]
                        shed["COW"] -= 1
                        unassigned.remove(w); continue
                    elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "SHEEP", 1]
                        shed["SHEEP"] -= 1
                        unassigned.remove(w); continue
                    elif unfed_animal_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                        take_qty = min(4, shed["WHEAT"])
                        actions[w] = ["PICKUP", "WHEAT", take_qty]
                        shed["WHEAT"] -= take_qty
                        unassigned.remove(w); continue

            # Pass 3: Targeted Spatial Routing
            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]
            claimed_unfed = set()

            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                # 1. Animal delivery to empty structure
                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    if empty_pastures:
                        target = min(empty_pastures, key=lambda p: _manhattan(w_p, p))
                        actions[w] = [_get_next_step(w_p, target, tiles)]
                        unassigned.remove(w); continue

                # 2. Worker carrying Wheat routes to unfed animal
                if inv.get("WHEAT", 0) > 0 and unfed_animal_tiles:
                    avail_unfed = [p for p in unfed_animal_tiles if p not in claimed_unfed]
                    target = min(avail_unfed or unfed_animal_tiles, key=lambda p: _manhattan(w_p, p))
                    claimed_unfed.add(target)
                    actions[w] = [_get_next_step(w_p, target, tiles)]
                    unassigned.remove(w); continue

                # 3. Worker without Wheat heads to shed if animals hungry
                if inv.get("WHEAT", 0) == 0 and unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                    if len(claimed_unfed) < len(unfed_animal_tiles) and unlocked_sheds:
                        actions[w] = [_get_next_step(w_p, unlocked_sheds[0], tiles)]
                        unassigned.remove(w); continue

            # Pass 4: General Chores & Fallback Routing
            for w in unassigned:
                w_p = worker_pos[w]
                if rem_chores:
                    best_c = None
                    best_score = -999999.0
                    for c in rem_chores:
                        dist = _manhattan(w_p, c["pos"])
                        score = c["weight"] - dist * 2.0
                        if score > best_score:
                            best_score = score
                            best_c = c
                    if best_c:
                        actions[w] = [_get_next_step(w_p, best_c["pos"], tiles)]
                        assigned_pos.add(best_c["pos"])
                        rem_chores.remove(best_c)
                        continue

                if w_p not in unlocked_sheds and unlocked_sheds:
                    actions[w] = [_get_next_step(w_p, unlocked_sheds[0], tiles)]
                else:
                    actions[w] = ["PASS"]

            return {
                "farmer": actions[0],
                "hands": actions[1:] if len(actions) > 1 else [],
                "market": orders[:10]
            }
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}


_default_compiler = DeclarativeBackboneCompiler(V54_PRIOR)


def agent(obs, configuration=None):
    return _default_compiler(obs, configuration)
