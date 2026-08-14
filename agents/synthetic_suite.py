"""
=============================================================================
SYNTHETIC OPPONENT SUITE
=============================================================================
Provides standalone bot archetypes discovered from actual Kaggle match replays
for comprehensive multi-archetype robustness benchmarking.
=============================================================================
"""

import math
from config import CROPS, ANIMALS, PRODUCTS, LAND_PRICES, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles


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
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]
            
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

            # 3. SEED PURCHASES BY ARCHETYPE
            empty_tiles = []
            chores = []
            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    if t is None:
                        empty_tiles.append((x, y))
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": (x, y), "weight": 90})
                        elif kind == "PLANT":
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": (x, y), "weight": 80})
                            if t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": (x, y), "weight": 100})

            needed_seeds = max(0, len(empty_tiles) - sum(seeds.values()))
            spendable = max(0.0, money - 30.0)

            if needed_seeds > 0 and day <= 26 and spendable > 0:
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
                else: # BALANCED
                    melon_cnt = min(needed_seeds, int(spendable // 80)) // 2
                    carrot_cnt = min(needed_seeds - melon_cnt, int((spendable - melon_cnt * 80) // 20))
                    if melon_cnt > 0: orders.append(["BUY_SEED", "MELON", melon_cnt])
                    if carrot_cnt > 0: orders.append(["BUY_SEED", "CARROT", carrot_cnt])

            # 4. SELLING
            for prod in PRODUCTS:
                qty = shed.get(prod, 0)
                if qty > 0 and (day >= 26 or step % 4 == 0):
                    orders.append(["SELL", prod, min(qty, 12)])

            # --- WORKER CHORES ---
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

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
                    elif t.get("kind") == "PLANT":
                        if t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                        elif not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w)
                elif t is None and day <= 26:
                    for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT"]:
                        if avail_seeds.get(sc, 0) > 0:
                            actions[w] = ["PLANT", sc]
                            avail_seeds[sc] -= 1
                            unassigned.remove(w)
                            break

            # Route remaining
            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            for w in unassigned:
                w_p = worker_pos[w]
                if chores:
                    best_c = min(chores, key=lambda c: manhattan(w_p, c["pos"]))
                    move = get_next_step(w_p, best_c["pos"], tiles)
                    actions[w] = [move]
                else:
                    if w_p not in unlocked_sheds:
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


# Factory functions for each archetype
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
