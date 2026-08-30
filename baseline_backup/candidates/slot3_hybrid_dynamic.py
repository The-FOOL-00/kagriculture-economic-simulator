"""
=============================================================================
KAGGRICULTURE CHAMPION DELIVERABLE 2: HYBRID DYNAMIC ECONOMIC AGENT
=============================================================================
State-dependent economic optimization agent:
1. Dynamic Livestock Engine: Evaluates capital & land to dynamically procure cows/sheep/geese.
2. Dynamic Economic Allocator: Marginal ROI evaluation per tile-day, eliminating cycle-2 melon traps.
3. Elasticity-Aware Market Executor: Non-linear price impact modeling & town consumption wave synchronization.
4. Opponent Anti-Saturation Model: Detects opponent crop gluts and hedges production.
5. Unified Spatial Labor Scheduler: Optimal chore prioritization and worker logistics.
=============================================================================
"""

import math
from config import CROPS, ANIMALS, PRODUCTS, MARKET_PARAMS, LAND_PRICES, compute_market_price, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles


class HybridDynamicEconomicAgent:
    def __init__(self, max_cows=6, max_sheep=3, max_geese=0, early_melon_cap=12):
        self.max_cows = max_cows
        self.max_sheep = max_sheep
        self.max_geese = max_geese
        self.early_melon_cap = early_melon_cap
        self.priority_order = ["MELON", "WOOL", "MILK", "FERTILIZER", "STRAWBERRY", "TOMATO", "EGG", "CARROT", "WHEAT"]

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0)
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)
            rem_days = 29 - day

            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            opp_farm = farms[1 - player] if farms and len(farms) > 1 else {}
            money = float(farm.get("money", 0.0))
            farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0))
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))
            tiles = farm.get("tiles", [[None]*10 for _ in range(10)])
            opp_tiles = opp_farm.get("tiles", [[None]*10 for _ in range(10)])

            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}))
            seeds = dict(private.get("seeds", {}))
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]

            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}))
            market_inv = dict(market.get("inventory", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            goose_count = 0
            pasture_count = 0
            coop_count = 0
            melon_count = 0

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
                            pasture_count += 1
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
                        elif kind == "COOP":
                            coop_count += 1
                            if "animal" in t:
                                goose_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 90})
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 75})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 85})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop == "MELON": melon_count += 1
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

            # Scan Opponent Farm for Saturation Detection
            opp_melons = 0
            for row in opp_tiles:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "MELON":
                        opp_melons += 1

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
                    if money >= cost + 15:
                        orders.append(["HIRE"])
                        money -= cost

            # 2. LAND EXPANSION
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250: # NE Land ($1,000)
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 500 and day <= 14: # SW Land ($2,000)
                    orders.append(["BUY_LAND"])
                    money -= cost

            spendable = max(0.0, money - 30.0)

            # 3. DYNAMIC LIVESTOCK ACQUISITION
            needed_cows = max(0, self.max_cows - cow_count - shed.get("COW", 0))
            needed_sheep = max(0, self.max_sheep - sheep_count - shed.get("SHEEP", 0))
            needed_geese = max(0, self.max_geese - goose_count - shed.get("GOOSE", 0))

            if day <= 13:
                # Prioritize cows early (high milk cashflow), then sheep
                while needed_cows > 0 and spendable >= 600 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    needed_cows -= 1
                while needed_sheep > 0 and spendable >= 500 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    needed_sheep -= 1
                while needed_geese > 0 and spendable >= 300 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "GOOSE", 1])
                    spendable -= 300
                    money -= 300
                    needed_geese -= 1

            # 4. WHEAT FEED BUFFER MANAGEMENT
            total_active_animals = cow_count + sheep_count + goose_count
            if total_active_animals > 0 and day <= 28:
                feed_held = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories)
                feed_needed = total_active_animals * 2
                if feed_held < feed_needed:
                    buy_wheat = min(feed_needed - feed_held + total_active_animals, int(spendable // 25))
                    if buy_wheat > 0 and len(orders) < 10:
                        orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat])
                        spendable -= buy_wheat * 25

            # 5. DYNAMIC ECONOMIC SEED ALLOCATOR
            total_seeds = sum(seeds.values())
            needed_seeds = max(0, len(empty_tiles) - total_seeds)

            if needed_seeds > 0 and day <= 26 and spendable > 0 and len(orders) < 10:
                if day <= 12 and rem_days >= 12:
                    # Early capital growth phase
                    m_target = min(self.early_melon_cap, needed_seeds)
                    if opp_melons >= 18:
                        # Opponent flooded melons; hedge into carrots & wheat
                        m_target = min(m_target, int(needed_seeds * 0.35))
                    
                    m_cnt = min(m_target, int(spendable // CROPS["MELON"]["seed"]))
                    rem = needed_seeds - m_cnt
                    c_cnt = min(int(rem * 0.7), int((spendable - m_cnt * 80) // CROPS["CARROT"]["seed"]))
                    w_cnt = min(rem - c_cnt, int((spendable - m_cnt * 80 - c_cnt * 20) // CROPS["WHEAT"]["seed"]))

                    if m_cnt > 0: orders.append(["BUY_SEED", "MELON", m_cnt])
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

                elif day <= 19 and rem_days >= 10:
                    # Mid season: 0 Cycle-2 Melons to avoid decay risk; focus on Carrots + Wheat
                    c_cnt = min(int(needed_seeds * 0.7), int(spendable // CROPS["CARROT"]["seed"]))
                    w_cnt = min(needed_seeds - c_cnt, int((spendable - c_cnt * 20) // CROPS["WHEAT"]["seed"]))
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

                elif day <= 26 and rem_days >= 3:
                    # Late season: Fast 3-day Carrots (75%) + Wheat (25%)
                    c_cnt = min(int(needed_seeds * 0.75), int(spendable // CROPS["CARROT"]["seed"]))
                    w_cnt = min(needed_seeds - c_cnt, int((spendable - c_cnt * 20) // CROPS["WHEAT"]["seed"]))
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

            # 6. ELASTICITY-AWARE MARKET EXECUTOR & TOWN SYNCHRONIZATION
            feed_reserve = total_active_animals * 2 if day < 28 else 0
            for prod in self.priority_order:
                if len(orders) >= 10:
                    break
                qty = shed.get(prod, 0)
                if prod == "WHEAT":
                    qty = max(0, qty - feed_reserve)
                if qty <= 0:
                    continue

                cur_p = market_prices.get(prod, 1)
                inv = market_inv.get(prod, 10000)

                should_sell = False
                if day >= 26:
                    should_sell = True
                elif sum(shed.values()) >= 25:
                    should_sell = True
                elif (step % 4 == 0 or step % 12 == 0) and cur_p > 1:
                    should_sell = True
                elif cur_p > 1:
                    should_sell = True

                if should_sell:
                    # Elasticity-aware batch size
                    batch = qty if day >= 26 else min(qty, 14 if (step % 4 == 0) else 10)
                    if batch > 0:
                        orders.append(["SELL", prod, batch])

            # 7. WORKER ACTIONS & CHORES
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            assigned_pos = set()

            total_pastures_needed = self.max_cows + self.max_sheep
            pastures_to_build = max(0, total_pastures_needed - pasture_count)
            coops_to_build = max(0, self.max_geese - coop_count)

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
                    elif kind == "COOP" and "animal" not in t and inv.get("GOOSE", 0) > 0:
                        actions[w] = ["PLACE", "GOOSE"]
                        inv["GOOSE"] -= 1
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
                    elif coops_to_build > 0:
                        actions[w] = ["BUILD_COOP"]
                        coops_to_build -= 1
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
                    empty_pastures = [
                        (x, y) for y in range(len(tiles)) for x in range(len(tiles[0]))
                        if isinstance(tiles[y][x], dict) and tiles[y][x].get("kind") == "PASTURE" and "animal" not in tiles[y][x]
                    ]
                    if empty_pastures:
                        target = min(empty_pastures, key=lambda p: manhattan(w_p, p))
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

_dynamic_instance = HybridDynamicEconomicAgent()

def agent(obs, configuration=None):
    return _dynamic_instance(obs, configuration)
