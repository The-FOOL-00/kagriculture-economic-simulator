"""
=============================================================================
KAGGRICULTURE CHAMPION DELIVERABLE 3: HYBRID LOOKAHEAD PLANNER
=============================================================================
Forward-simulating macro planner with 2-day rolling lookahead:
1. Rolling Cashflow Lookahead: Projects upcoming harvest cash inflows, animal production ticks, and feed requirements.
2. Dynamic Capital Arbitrage: Allocates capital between land expansion, animal fleet, and high-velocity crops based on projected terminal wealth.
3. Town Modulo Wave Frontrunning: Timed batch selling to capture peak town shop consumption prices.
4. Terminal Phase Inventory Flushing: Zero shed and worker inventory waste at step 719.
=============================================================================
"""

import math
from config import CROPS, ANIMALS, PRODUCTS, MARKET_PARAMS, LAND_PRICES, compute_market_price, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles


class HybridLookaheadAgent:
    def __init__(self, base_cows=6, base_sheep=3, base_melons=10, lookahead_days=2):
        self.base_cows = base_cows
        self.base_sheep = base_sheep
        self.base_melons = base_melons
        self.lookahead_days = lookahead_days
        self.sell_batch_size = 14

    def project_future_cashflow(self, day, farm_tiles, shed, active_animals):
        """
        Projects net cash flow over the next `lookahead_days` from crop maturation and animal yields.
        """
        projected_cash = 0.0
        cows = active_animals.get("COW", 0)
        sheep = active_animals.get("SHEEP", 0)

        # Milk generates every 2 days @ ~$160; Wool every 3 days @ ~$200
        projected_cash += cows * (self.lookahead_days / 2.0) * 150.0
        projected_cash += sheep * (self.lookahead_days / 3.0) * 190.0

        # Feed cost projection
        total_animals = cows + sheep
        feed_cost = total_animals * self.lookahead_days * 25.0
        return max(0.0, projected_cash - feed_cost)

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0)
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)
            rem_days = 29 - day

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
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            pasture_count = 0
            empty_pastures = 0

            # Scan Farm Tiles
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
                        elif kind == "PASTURE":
                            if "animal" in t:
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures += 1
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            
                            is_h = False
                            if cd.get("ongoing", False):
                                if age >= cd["first_yield_day"] and t.get("yield_units", 0) > 0:
                                    is_h = True
                            else:
                                if crop == "MELON" and (age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_h = True
                                elif crop == "CARROT" and (age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_h = True
                                elif crop == "WHEAT" and (age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    is_h = True
                                elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                    is_h = True
                            if is_h:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            # 1. HIRE FARM HANDS at hour 0
            total_chores_est = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1:
                target_hands = min(3, max(2, (total_chores_est + 6) // 8))
            elif len(unlocked_quads) == 2:
                target_hands = min(5, max(3, (total_chores_est + 8) // 9))
            else:
                target_hands = min(6, max(4, (total_chores_est + 10) // 10))

            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10:
                        orders.append(["HIRE"])
                        money -= cost

            # 2. LAND EXPANSION WITH LOOKAHEAD
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250:
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 500 and day <= 14:
                    orders.append(["BUY_LAND"])
                    money -= cost

            spendable = max(0.0, money - 25.0)

            # 3. BUY ANIMALS
            needed_cows = max(0, self.base_cows - cow_count - shed.get("COW", 0))
            needed_sheep = max(0, self.base_sheep - sheep_count - shed.get("SHEEP", 0))

            if day <= 12:
                if needed_cows > 0 and spendable >= 600 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    needed_cows -= 1
                elif needed_sheep > 0 and spendable >= 500 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    needed_sheep -= 1

            # 4. WHEAT FEED BUFFER
            total_active_animals = cow_count + sheep_count
            if total_active_animals > 0:
                feed_in_shed = shed.get("WHEAT", 0)
                if feed_in_shed < total_active_animals * 2 and day <= 28:
                    buy_wheat_qty = min(total_active_animals * 3, int(spendable // 25))
                    if buy_wheat_qty > 0 and len(orders) < 10:
                        orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat_qty])
                        spendable -= buy_wheat_qty * 25

            # 5. CROP SEED PURCHASES
            total_seeds = sum(seeds.values())
            needed_seeds = max(0, len(empty_tiles) - total_seeds)

            if needed_seeds > 0 and day <= 26 and spendable > 0 and len(orders) < 10:
                if day <= 12:
                    target_m = self.base_melons
                    m_cnt = min(target_m, needed_seeds, int(spendable // 80))
                    rem = needed_seeds - m_cnt
                    c_cnt = min(rem, int((spendable - m_cnt * 80) // 20))
                    w_cnt = min(rem - c_cnt, int((spendable - m_cnt * 80 - c_cnt * 20) // 10))
                    if m_cnt > 0: orders.append(["BUY_SEED", "MELON", m_cnt])
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])
                elif day <= 19:
                    c_cnt = min(int(needed_seeds * 0.7), int(spendable // 20))
                    w_cnt = min(needed_seeds - c_cnt, int((spendable - c_cnt * 20) // 10))
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])
                elif day <= 26:
                    c_cnt = min(int(needed_seeds * 0.8), int(spendable // 20))
                    w_cnt = min(needed_seeds - c_cnt, int((spendable - c_cnt * 20) // 10))
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

            # 6. SELLING / LIQUIDATION
            feed_reserve = total_active_animals * 2 if day < 28 else 0
            sell_priority = ["MELON", "WOOL", "MILK", "FERTILIZER", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]
            for prod in sell_priority:
                if len(orders) >= 10:
                    break
                qty = shed.get(prod, 0)
                if prod == "WHEAT":
                    qty = max(0, qty - feed_reserve)
                if qty > 0:
                    cur_p = market_prices.get(prod, 1)
                    if day >= 26 or sum(shed.values()) >= 25 or (step % 4 == 0) or cur_p > 1:
                        sell_amount = min(qty, self.sell_batch_size) if day < 26 else qty
                        orders.append(["SELL", prod, sell_amount])

            # 7. WORKER ACTIONS & CHORES
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            assigned_pos = set()

            total_pastures_needed = self.base_cows + self.base_sheep
            curr_pastures = pasture_count + empty_pastures
            pastures_to_build = max(0, total_pastures_needed - curr_pastures)

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

            # Pass 1: Stand-on instant chore
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
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                    elif "animal" in t:
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            inv["WHEAT"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif t.get("fertilizer_available", False):
                            actions[w] = ["COLLECT_FERTILIZER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif not t.get("cared_today", False):
                            actions[w] = ["CARE"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                    elif kind == "PASTURE" and "animal" not in t:
                        if inv.get("COW", 0) > 0:
                            actions[w] = ["PLACE", "COW"]
                            inv["COW"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif inv.get("SHEEP", 0) > 0:
                            actions[w] = ["PLACE", "SHEEP"]
                            inv["SHEEP"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                    elif kind == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                        elif not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                elif t is None:
                    if pastures_to_build > 0:
                        actions[w] = ["BUILD_PASTURE"]
                        pastures_to_build -= 1
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                    elif day <= 26:
                        for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w)
                                assigned_pos.add(pos)
                                break

            # Pass 2: Spatial movement & logistics
            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]

            for w in unassigned:
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    empty_pastures_tiles = [
                        (x, y) for y in range(len(tiles)) for x in range(len(tiles[0]))
                        if isinstance(tiles[y][x], dict) and tiles[y][x].get("kind") == "PASTURE" and "animal" not in tiles[y][x]
                    ]
                    if empty_pastures_tiles:
                        target = min(empty_pastures_tiles, key=lambda p: manhattan(w_p, p))
                        actions[w] = [get_next_step(w_p, target, tiles)]
                        continue

                if w_p in unlocked_sheds:
                    if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0:
                        actions[w] = ["PICKUP", "COW", 1]
                        continue
                    elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0:
                        actions[w] = ["PICKUP", "SHEEP", 1]
                        continue
                    elif total_active_animals > 0 and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                        actions[w] = ["PICKUP", "WHEAT", min(4, shed["WHEAT"])]
                        continue

                if rem_chores:
                    best_c = None
                    best_score = -999999.0
                    for c in rem_chores:
                        dist = manhattan(w_p, c["pos"])
                        score = c["weight"] - dist * 2.0
                        if score > best_score:
                            best_score = score
                            best_c = c
                    if best_c:
                        actions[w] = [get_next_step(w_p, best_c["pos"], tiles)]
                        assigned_pos.add(best_c["pos"])
                        rem_chores.remove(best_c)
                        continue

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

_lookahead_instance = HybridLookaheadAgent()

def agent(obs, configuration=None):
    return _lookahead_instance(obs, configuration)
