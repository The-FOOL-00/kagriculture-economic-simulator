"""
=============================================================================
SYNTHETIC OPPONENT SUITE (CORRECTED & ROBUST)
=============================================================================
Provides standalone bot archetypes discovered from actual Kaggle match replays
for comprehensive multi-archetype robustness benchmarking.
=============================================================================
"""

import math

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 4},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False, "base_yield": 3},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 6},
}

LAND_PRICES = [1000, 2000, 4000]
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]


def fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_unlocked_shed_tiles(tiles):
    half = len(tiles) // 2
    candidates = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]


def get_next_step(start, target, tiles):
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target
    moves = []
    if tx > sx and tiles[sy][sx + 1] != "LOCKED": moves.append("EAST")
    if tx < sx and tiles[sy][sx - 1] != "LOCKED": moves.append("WEST")
    if ty > sy and tiles[sy + 1][sx] != "LOCKED": moves.append("SOUTH")
    if ty < sy and tiles[sy - 1][sx] != "LOCKED": moves.append("NORTH")
    
    if not moves:
        for m, (dx, dy) in [("EAST", (1,0)), ("WEST", (-1,0)), ("SOUTH", (0,1)), ("NORTH", (0,-1))]:
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles) and tiles[ny][nx] != "LOCKED":
                moves.append(m)
    return moves[0] if moves else "PASS"


class SyntheticArchetypeAgent:
    def __init__(self, archetype="BALANCED"):
        self.archetype = archetype

    def __call__(self, obs):
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
            tiles = farm.get("tiles", [[None]*10 for _ in range(10)])
            
            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}))
            seeds = dict(private.get("seeds", {}))
            
            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}))

            orders = []
            
            # --- MARKET ORDERS ---
            # 1. HIRE at hour 0
            target_workers = 4 if len(unlocked_quads) == 1 else 5
            target_hands = target_workers - 1
            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost:
                        orders.append(["HIRE"])
                        money -= cost

            # 2. LAND EXPANSION
            n_unlocked = len(unlocked_quads) - 1
            if self.archetype == "LAND_EXPANSION" and n_unlocked < 3:
                cost = LAND_PRICES[n_unlocked]
                if money >= cost + 100:
                    orders.append(["BUY_LAND"])
                    money -= cost
            elif n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250:
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 600 and day <= 14:
                    orders.append(["BUY_LAND"])
                    money -= cost

            # 3. SCAN TILES FOR CHORES & MATURITY
            empty_tiles = []
            chores = []
            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    pos = (x, y)
                    if t is None:
                        empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": pos, "weight": 90})
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 80})

                            is_mature = False
                            if cd.get("ongoing", False):
                                if age >= cd["first_yield_day"] and t.get("yield_units", 0) > 0:
                                    is_mature = True
                            else:
                                if crop == "MELON" and (age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_mature = True
                                elif crop == "CARROT" and (age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_mature = True
                                elif crop == "WHEAT" and (age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_mature = True
                                elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                    is_mature = True

                            if is_mature:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            # 4. SEED PURCHASES BY ARCHETYPE
            needed_seeds = max(0, len(empty_tiles) - sum(seeds.values()))
            spendable = max(0.0, money - 30.0)

            if needed_seeds > 0 and day <= 26 and spendable > 0 and len(orders) < 10:
                if self.archetype == "MELON_BURST":
                    p_crop = "MELON" if day <= 18 else "CARROT"
                    price = CROPS[p_crop]["seed"]
                    buy_cnt = min(needed_seeds, int(spendable // price))
                    if buy_cnt > 0:
                        orders.append(["BUY_SEED", p_crop, buy_cnt])
                elif self.archetype == "STRAWBERRY_RUSH":
                    p_crop = "STRAWBERRY" if day <= 18 else "CARROT"
                    price = CROPS[p_crop]["seed"]
                    buy_cnt = min(needed_seeds, int(spendable // price))
                    if buy_cnt > 0:
                        orders.append(["BUY_SEED", p_crop, buy_cnt])
                elif self.archetype == "CROP_EFFICIENT":
                    p_crop = "CARROT" if day <= 25 else "WHEAT"
                    price = CROPS[p_crop]["seed"]
                    buy_cnt = min(needed_seeds, int(spendable // price))
                    if buy_cnt > 0:
                        orders.append(["BUY_SEED", p_crop, buy_cnt])
                else:  # BALANCED
                    melon_cnt = min(needed_seeds, int(spendable // 80)) // 2 if day <= 12 else 0
                    carrot_cnt = min(needed_seeds - melon_cnt, int((spendable - melon_cnt * 80) // 20))
                    if melon_cnt > 0: orders.append(["BUY_SEED", "MELON", melon_cnt])
                    if carrot_cnt > 0: orders.append(["BUY_SEED", "CARROT", carrot_cnt])

            # 5. SELLING
            for prod in PRODUCTS:
                if len(orders) >= 10:
                    break
                qty = shed.get(prod, 0)
                if qty > 0 and (day >= 26 or sum(shed.values()) >= 20 or step % 4 == 0):
                    orders.append(["SELL", prod, min(qty, 14) if day < 26 else qty])

            # --- WORKER CHORES ---
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            assigned_pos = set()

            # Stand on chore
            avail_seeds = dict(seeds)
            for w in list(unassigned):
                pos = worker_pos[w]
                x, y = pos
                t = tiles[y][x]
                if isinstance(t, dict):
                    if t.get("kind") == "WEED":
                        actions[w] = ["DIG"]
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                    elif t.get("kind") == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                elif t is None and day <= 26:
                    for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                        if avail_seeds.get(sc, 0) > 0:
                            actions[w] = ["PLANT", sc]
                            avail_seeds[sc] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            break

            # Route remaining workers to chores
            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]

            for w in unassigned:
                w_p = worker_pos[w]
                if rem_chores:
                    best_c = min(rem_chores, key=lambda c: manhattan(w_p, c["pos"]))
                    move = get_next_step(w_p, best_c["pos"], tiles)
                    actions[w] = [move]
                    assigned_pos.add(best_c["pos"])
                    rem_chores.remove(best_c)
                else:
                    if w_p not in unlocked_sheds and unlocked_sheds:
                        actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                    else:
                        actions[w] = ["PASS"]

            return {
                "farmer": actions[0],
                "hands": actions[1:] if len(actions) > 1 else [],
                "market": orders[:10]
            }
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}


def melon_burst_agent(obs):
    return SyntheticArchetypeAgent("MELON_BURST")(obs)

def strawberry_rush_agent(obs):
    return SyntheticArchetypeAgent("STRAWBERRY_RUSH")(obs)

def crop_efficient_agent(obs):
    return SyntheticArchetypeAgent("CROP_EFFICIENT")(obs)

def land_expansion_agent(obs):
    return SyntheticArchetypeAgent("LAND_EXPANSION")(obs)

def balanced_agent(obs):
    return SyntheticArchetypeAgent("BALANCED")(obs)
