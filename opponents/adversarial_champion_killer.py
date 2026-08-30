"""
=============================================================================
ADVERSARIAL CHAMPION KILLER (OBJECTIVES 3 & 4)
=============================================================================
An active, predatory adversarial counterstrategy specifically designed to
maximize win rate / loss probability against Hybrid 8C/4S/15M:

1. WHEAT MARKET CORNERING (FEED SQUEEZE):
   - Purchases extra wheat inventory on Days 0-2 to drive up market price
     and force the opponent into expensive feed purchases.
2. HOMEGROWN FEED IMMUNITY:
   - Plants 6 dedicated Wheat plots on Day 0 so the adversary is 100% immune
     to wheat market scarcity.
3. MELON MARKET GLUT & FRONTRUNNING:
   - Plants 12-16 early Melons and harvests/sells at Day 10-11 (step % 4 == 3),
     frontrunning our Day 12 liquidation and collapsing Melon spot price.
4. TARGETED LIVESTOCK SCALING:
   - Operates a lean 6C / 4S / 0G fleet financed by homegrown wheat.
5. PREDICTIVE TACTICAL DISPATCH:
   - High-throughput chore scheduler with strict priority on weed eradication
     and zero animal starvation.
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

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 600, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
PRICE_FLOOR = 1

def fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a + b
    return a

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def get_unlocked_shed_tiles(tiles):
    half = len(tiles) // 2
    candidates = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]

def get_next_step(start, target, tiles):
    if start == target: return "PASS"
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

class AdversarialChampionKiller:
    def __init__(self, target_cows=8, target_sheep=4, target_melons=14, target_wheat_plots=6, predatory_frontrun=True):
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = 0
        self.target_melons = target_melons
        self.target_wheat_plots = target_wheat_plots
        self.predatory_frontrun = predatory_frontrun
        self.sell_batch_size = 14

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0)
            opp_player = 1 - player
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)

            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            opp_farm = farms[opp_player] if farms and opp_player < len(farms) else {}

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
            market_inv = dict(market.get("inventory", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            pasture_count = 0
            empty_pastures = []
            melon_plants = 0
            wheat_plants = 0
            carrot_plants = 0
            unfed_animal_tiles = []

            # 1. Scan Tiles
            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    pos = (x, y)
                    if t is None:
                        empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": pos, "weight": 98})
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 95})
                                    unfed_animal_tiles.append(pos)
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop == "MELON": melon_plants += 1
                            elif crop == "WHEAT": wheat_plants += 1
                            elif crop == "CARROT": carrot_plants += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 84})
                            if crop == "MELON":
                                # Harvest as soon as day 10 or 6 units to frontrun
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 3 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 96})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + cows_in_transit + sheep_in_transit

            # 2. Labor Hiring
            total_work_load = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1: target_hands = min(3, max(2, (total_work_load + 6) // 8))
            elif len(unlocked_quads) == 2: target_hands = min(5, max(3, (total_work_load + 8) // 9))
            else: target_hands = min(6, max(4, (total_work_load + 10) // 10))

            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10:
                        orders.append(["HIRE"])
                        money -= cost

            # 3. Land Purchase
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked == 0 and money >= 1250:
                orders.append(["BUY_LAND"])
                money -= 1000
            elif n_unlocked == 1 and money >= 2800 and day <= 14:
                orders.append(["BUY_LAND"])
                money -= 2000

            spendable = max(0.0, money - 30.0)

            # 4. Animal Purchases
            needed_cows = max(0, self.target_cows - cow_count - cows_in_transit)
            needed_sheep = max(0, self.target_sheep - sheep_count - sheep_in_transit)
            cows_ordered = 0
            sheep_ordered = 0

            if day <= 12:
                if needed_cows > 0 and spendable >= 690 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    cows_ordered += 1
                if needed_sheep > 0 and spendable >= 590 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    sheep_ordered += 1

            # 5. Feed Reserve & Strategic Wheat Cornering
            tot_animals = total_active_animals + cows_ordered + sheep_ordered
            feed_needed = tot_animals * (4 if day < 26 else 0)
            wheat_in_shed = shed.get("WHEAT", 0)
            
            # On Day 0-1, aggressively buy extra wheat to corner the feed market against opponent
            if day <= 1:
                feed_target = feed_needed + 8  # Corner market
            else:
                feed_target = feed_needed

            if wheat_in_shed < feed_target and spendable >= 30 and len(orders) < 10:
                w_price = market_prices.get("WHEAT", 25)
                deficit = feed_target - wheat_in_shed
                max_w = int(spendable // max(1, w_price))
                buy_w = min(deficit, max_w, 20)
                if buy_w > 0:
                    orders.append(["BUY", "WHEAT", buy_w])
                    spendable -= buy_w * w_price
                    money -= buy_w * w_price

            # 6. Seed Purchasing
            # Dedicated Homegrown Wheat Plots
            if day <= 24 and (wheat_plants + seeds.get("WHEAT", 0)) < self.target_wheat_plots and spendable >= 15 and len(orders) < 10:
                w_seed_needed = self.target_wheat_plots - (wheat_plants + seeds.get("WHEAT", 0))
                can_buy = min(w_seed_needed, int(spendable // 10), 10)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy])
                    spendable -= can_buy * 10
                    money -= can_buy * 10

            # Early Melons
            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.target_melons and spendable >= 90 and len(orders) < 10:
                m_needed = self.target_melons - (melon_plants + seeds.get("MELON", 0))
                can_buy = min(m_needed, int(spendable // 80), 10)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy])
                    spendable -= can_buy * 80
                    money -= can_buy * 80

            # Carrots for fast cash velocity
            if day >= 3 and day <= 26 and (carrot_plants + seeds.get("CARROT", 0)) < 12 and spendable >= 30 and len(orders) < 10:
                c_needed = 12 - (carrot_plants + seeds.get("CARROT", 0))
                can_buy = min(c_needed, int(spendable // 20), 10)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "CARROT", can_buy])
                    spendable -= can_buy * 20
                    money -= can_buy * 20

            # 7. Frontrunning & Liquidation Market Execution
            # Sell on step % 4 == 0 (town post-consumption) OR step % 4 == 3 (predatory frontrun before opponent)
            should_sell = (step % 4 == 0) or (self.predatory_frontrun and (step % 4 == 3)) or (step >= 680)
            if should_sell:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.sell_batch_size if step < 680 else 30)
                        orders.append(["SELL", prod, batch])

            # 8. Labor Dispatch
            unplaced_pasture = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            pastures_needed = max(0, min(self.target_cows + self.target_sheep - pasture_count, unplaced_pasture - len(empty_pastures)))

            workers = [farmer_pos] + hands
            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            actions = [["PASS"] for _ in range(len(workers))]
            rem_chores = list(chores)
            assigned_targets = set()

            for w, w_p in enumerate(workers):
                # Build pasture if needed and on empty tile
                if pastures_needed > 0 and tiles[w_p[1]][w_p[0]] is None and w_p not in assigned_targets:
                    actions[w] = ["BUILD_PASTURE"]
                    pastures_needed -= 1
                    assigned_targets.add(w_p)
                    continue

                # Planting
                if tiles[w_p[1]][w_p[0]] is None and w_p not in assigned_targets:
                    if seeds.get("WHEAT", 0) > 0 and wheat_plants < self.target_wheat_plots:
                        actions[w] = ["PLANT", "WHEAT"]
                        seeds["WHEAT"] -= 1
                        wheat_plants += 1
                        assigned_targets.add(w_p)
                        continue
                    elif seeds.get("MELON", 0) > 0 and melon_plants < self.target_melons:
                        actions[w] = ["PLANT", "MELON"]
                        seeds["MELON"] -= 1
                        melon_plants += 1
                        assigned_targets.add(w_p)
                        continue
                    elif seeds.get("CARROT", 0) > 0:
                        actions[w] = ["PLANT", "CARROT"]
                        seeds["CARROT"] -= 1
                        carrot_plants += 1
                        assigned_targets.add(w_p)
                        continue

                # Chore execution
                best_c = None
                best_score = -999999
                for c in rem_chores:
                    if c["pos"] in assigned_targets: continue
                    dist = manhattan(w_p, c["pos"])
                    score = c["weight"] * 10 - dist * 4
                    if score > best_score:
                        best_score = score
                        best_c = c

                if best_c:
                    if w_p == best_c["pos"]:
                        act_type = best_c["type"]
                        if act_type == "WATER": actions[w] = ["WATER"]
                        elif act_type == "FEED": actions[w] = ["FEED"]
                        elif act_type == "CARE": actions[w] = ["CARE"]
                        elif act_type == "HARVEST": actions[w] = ["HARVEST"]
                        elif act_type == "DIG": actions[w] = ["DIG"]
                        elif act_type == "COLLECT_FERTILIZER": actions[w] = ["COLLECT_FERTILIZER"]
                        assigned_targets.add(w_p)
                        rem_chores.remove(best_c)
                        continue
                    else:
                        step_dir = get_next_step(w_p, best_c["pos"], tiles)
                        actions[w] = [step_dir]
                        assigned_targets.add(best_c["pos"])
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

_killer_instance = AdversarialChampionKiller()
def agent(obs, configuration=None):
    return _killer_instance(obs, configuration)
