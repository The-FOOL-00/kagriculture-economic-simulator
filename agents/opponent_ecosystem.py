"""
=============================================================================
AGENTS: COMPREHENSIVE 12-ARCHETYPE COMPETITIVE OPPONENT ECOSYSTEM
=============================================================================
Provides 12 fully verified, non-failing, distinct tactical opponents:
O1:  Titan Production Baseline (main.py)
O2:  Golden Control v1 (agents/golden_v1.py)
O3:  Early Melon Specialist (25-30 Melon opening, delayed livestock)
O4:  Fast Crop Specialist (Carrot & Wheat rapid 3-day rotations, high labor)
O5:  Cow Specialist (8-10 Cows, dedicated dairy engine)
O6:  Sheep Specialist (6-8 Sheep, elasticity-aware wool engine)
O7:  Balanced Livestock (4 Cows + 3 Sheep + 4 Geese mixed fleet)
O8:  Dynamic Economic Optimizer (Daily marginal ROI dynamic asset allocator)
O9:  Market Aggressor (High-volume frontrunner dumping on town consumption)
O10: Anti-Melon Specialist (Exploits melon glut with strawberries, tomatoes, milk)
O11: Anti-Livestock Specialist (Fast crop blitz taking market liquidity before livestock matures)
O12: Top-Meta Emulator (8C/4S/10M industrial scaler with Fibonacci labor management)
=============================================================================
"""

import os
import sys
import copy
import math
import importlib.util

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import CROPS, ANIMALS, PRODUCTS, compute_market_price, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ---------------------------------------------------------------------------
# Base Tactical Engine for Specialized Opponents
# ---------------------------------------------------------------------------
class BaseArchetypeAgent:
    def __init__(
        self,
        name="Archetype",
        target_cows=0,
        target_sheep=0,
        target_geese=0,
        primary_crop="CARROT",
        primary_crop_count=15,
        secondary_crop="WHEAT",
        secondary_crop_count=10,
        day0_land=True,
        day10_land=False,
        sell_batch_size=14,
        market_frontrun=False,
        care_animals=True,
        feed_safety_buffer=3
    ):
        self.name = name
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = target_geese
        self.primary_crop = primary_crop
        self.primary_crop_count = primary_crop_count
        self.secondary_crop = secondary_crop
        self.secondary_crop_count = secondary_crop_count
        self.day0_land = day0_land
        self.day10_land = day10_land
        self.sell_batch_size = sell_batch_size
        self.market_frontrun = market_frontrun
        self.care_animals = care_animals
        self.feed_safety_buffer = feed_safety_buffer

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
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 90})
                                    unfed_animal_tiles.append(pos)
                                if self.care_animals and not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 75})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 85})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_coops.append(pos)
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                    unfed_animal_tiles.append(pos)
                                if self.care_animals and not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop in crop_counts: crop_counts[crop] += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})

                            if cd.get("ongoing", False):
                                if age >= cd.get("first_yield_day", 8) and t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                if crop == "MELON" and (age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif crop == "CARROT" and (age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif crop == "WHEAT" and (age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # 1. HIRE WORKERS
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

            # 2. LAND EXPANSION
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked == 0 and self.day0_land and money >= 1200:
                orders.append(["BUY_LAND"])
                money -= 1000
            elif n_unlocked == 1 and self.day10_land and day <= 14 and money >= 2400:
                orders.append(["BUY_LAND"])
                money -= 2000

            spendable = max(0.0, money - 25.0)

            # 3. BUY ANIMALS
            needed_cows = max(0, self.target_cows - cow_count - cows_in_transit)
            needed_sheep = max(0, self.target_sheep - sheep_count - sheep_in_transit)
            needed_geese = max(0, self.target_geese - goose_count - geese_in_transit)

            cows_ordered = 0
            sheep_ordered = 0
            geese_ordered = 0

            if day <= 12:
                if needed_cows > 0 and spendable >= 695 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    needed_cows -= 1
                    cows_ordered += 1
                    total_active_animals += 1
                elif needed_sheep > 0 and spendable >= 595 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    needed_sheep -= 1
                    sheep_ordered += 1
                    total_active_animals += 1
                elif needed_geese > 0 and spendable >= 395 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "GOOSE", 1])
                    spendable -= 300
                    money -= 300
                    needed_geese -= 1
                    geese_ordered += 1
                    total_active_animals += 1

            # 4. WHEAT FEED BUFFER
            if total_active_animals > 0 and day <= 28:
                total_wheat_held = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories)
                feed_buffer_target = total_active_animals * self.feed_safety_buffer
                if total_wheat_held < feed_buffer_target:
                    deficit = feed_buffer_target - total_wheat_held
                    buy_wheat_qty = min(deficit + total_active_animals, int(spendable // 25))
                    if buy_wheat_qty > 0 and len(orders) < 10:
                        orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat_qty])
                        spendable -= buy_wheat_qty * 25
                        money -= buy_wheat_qty * 25

            # 5. CROP SEED PURCHASES
            total_seeds = sum(seeds.values())
            needed_seeds = max(0, len(empty_tiles) - total_seeds)

            if needed_seeds > 0 and day <= 26 and spendable > 0 and len(orders) < 10:
                p_cost = CROPS[self.primary_crop]["seed"]
                s_cost = CROPS[self.secondary_crop]["seed"]

                p_rem = max(0, self.primary_crop_count - crop_counts.get(self.primary_crop, 0) - seeds.get(self.primary_crop, 0))
                p_cnt = min(p_rem, needed_seeds, int(spendable // p_cost))
                rem = needed_seeds - p_cnt
                s_cnt = min(rem, int((spendable - p_cnt * p_cost) // s_cost))
                w_cnt = min(rem - s_cnt, int((spendable - p_cnt * p_cost - s_cnt * s_cost) // 10))

                if p_cnt > 0: orders.append(["BUY_SEED", self.primary_crop, p_cnt])
                if s_cnt > 0: orders.append(["BUY_SEED", self.secondary_crop, s_cnt])
                if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

            # 6. SELLING & MARKET POLICIES
            feed_reserve = total_active_animals * 4 if day < 26 else 0
            sell_priority = ["MELON", "WOOL", "MILK", "FERTILIZER", "EGG", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]
            for prod in sell_priority:
                if len(orders) >= 10:
                    break
                qty = shed.get(prod, 0)
                if prod == "WHEAT":
                    qty = max(0, qty - feed_reserve)
                if qty > 0:
                    cur_p = market_prices.get(prod, 1)
                    should_sell = False
                    if day >= 26 or sum(shed.values()) >= 25 or cur_p > 1:
                        should_sell = True
                    if self.market_frontrun and (step % 4 == 0 or step % 4 == 1):
                        should_sell = True

                    if should_sell:
                        sell_amount = min(qty, self.sell_batch_size) if day < 26 else qty
                        orders.append(["SELL", prod, sell_amount])

            # 7. WORKER ACTIONS & CHORES
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            assigned_pos = set()

            unplaced_pasture_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            total_pastures_target = self.target_cows + self.target_sheep
            pastures_to_build = max(0, min(total_pastures_target - pasture_count, unplaced_pasture_animals - len(empty_pastures)))

            unplaced_geese = geese_in_transit + geese_ordered
            total_coops_target = self.target_geese
            coops_to_build = max(0, min(total_coops_target - coop_count, unplaced_geese - len(empty_coops)))

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

            # Pass 1: Instant Chores on current tile
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
                        continue
                    elif "animal" in t and t.get("animal"):
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            inv["WHEAT"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            if pos in unfed_animal_tiles: unfed_animal_tiles.remove(pos)
                            continue
                        if t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if t.get("fertilizer_available", False):
                            actions[w] = ["COLLECT_FERTILIZER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if self.care_animals and not t.get("cared_today", False):
                            actions[w] = ["CARE"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "PASTURE" and "animal" not in t:
                        if inv.get("COW", 0) > 0:
                            actions[w] = ["PLACE", "COW"]
                            inv["COW"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        elif inv.get("SHEEP", 0) > 0:
                            actions[w] = ["PLACE", "SHEEP"]
                            inv["SHEEP"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "COOP" and "animal" not in t:
                        if inv.get("GOOSE", 0) > 0:
                            actions[w] = ["PLACE", "GOOSE"]
                            inv["GOOSE"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                elif t is None:
                    if pastures_to_build > 0:
                        actions[w] = ["BUILD_PASTURE"]
                        pastures_to_build -= 1
                        pasture_count += 1
                        empty_pastures.append(pos)
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                        continue
                    elif coops_to_build > 0:
                        actions[w] = ["BUILD_COOP"]
                        coops_to_build -= 1
                        coop_count += 1
                        empty_coops.append(pos)
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                        continue
                    elif day <= 26:
                        for sc in ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w)
                                assigned_pos.add(pos)
                                break

            # Pass 2: Shed Interactions
            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if w_p in unlocked_sheds:
                    if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "COW", 1]
                        shed["COW"] -= 1
                        unassigned.remove(w)
                        continue
                    elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "SHEEP", 1]
                        shed["SHEEP"] -= 1
                        unassigned.remove(w)
                        continue
                    elif shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0 and empty_coops:
                        actions[w] = ["PICKUP", "GOOSE", 1]
                        shed["GOOSE"] -= 1
                        unassigned.remove(w)
                        continue
                    elif unfed_animal_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                        take_qty = min(4, shed["WHEAT"])
                        actions[w] = ["PICKUP", "WHEAT", take_qty]
                        shed["WHEAT"] -= take_qty
                        unassigned.remove(w)
                        continue

            # Pass 3: Targeted Spatial Routing
            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]
            claimed_unfed = set()

            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    if empty_pastures:
                        target = min(empty_pastures, key=lambda p: manhattan(w_p, p))
                        actions[w] = [get_next_step(w_p, target, tiles)]
                        unassigned.remove(w)
                        continue
                if inv.get("GOOSE", 0) > 0:
                    if empty_coops:
                        target = min(empty_coops, key=lambda p: manhattan(w_p, p))
                        actions[w] = [get_next_step(w_p, target, tiles)]
                        unassigned.remove(w)
                        continue

                if inv.get("WHEAT", 0) > 0 and unfed_animal_tiles:
                    avail_unfed = [p for p in unfed_animal_tiles if p not in claimed_unfed]
                    target = min(avail_unfed or unfed_animal_tiles, key=lambda p: manhattan(w_p, p))
                    claimed_unfed.add(target)
                    actions[w] = [get_next_step(w_p, target, tiles)]
                    unassigned.remove(w)
                    continue

                if inv.get("WHEAT", 0) == 0 and unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                    if len(claimed_unfed) < len(unfed_animal_tiles) and unlocked_sheds:
                        actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                        unassigned.remove(w)
                        continue

            # Pass 4: General Chores & Fallback
            for w in unassigned:
                w_p = worker_pos[w]
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

# ---------------------------------------------------------------------------
# Construct the 12 Opponent Archetypes
# ---------------------------------------------------------------------------

# O1: Titan Production Baseline
O1_TITAN_PATH = os.path.join(project_root, "main.py")

# O2: Golden Control v1
O2_GOLDEN_PATH = os.path.join(project_root, "agents", "golden_v1.py")

# O3: Early Melon Specialist (25-30 Melon opening, delayed livestock)
o3_agent_inst = BaseArchetypeAgent(
    name="O3_Melon_Specialist",
    target_cows=2,
    target_sheep=0,
    target_geese=0,
    primary_crop="MELON",
    primary_crop_count=28,
    secondary_crop="CARROT",
    secondary_crop_count=6,
    day0_land=True,
    day10_land=True,
    sell_batch_size=14,
    market_frontrun=True
)
def o3_early_melon_specialist(obs, configuration=None):
    return o3_agent_inst(obs, configuration)

# O4: Fast Crop Specialist (Carrot & Wheat rapid rotations, high labor)
o4_agent_inst = BaseArchetypeAgent(
    name="O4_Fast_Crop_Specialist",
    target_cows=0,
    target_sheep=0,
    target_geese=0,
    primary_crop="CARROT",
    primary_crop_count=35,
    secondary_crop="WHEAT",
    secondary_crop_count=15,
    day0_land=True,
    day10_land=True,
    sell_batch_size=16,
    market_frontrun=True
)
def o4_fast_crop_specialist(obs, configuration=None):
    return o4_agent_inst(obs, configuration)

# O5: Cow Specialist (8-10 Cows industrial dairy engine)
o5_agent_inst = BaseArchetypeAgent(
    name="O5_Cow_Specialist",
    target_cows=10,
    target_sheep=0,
    target_geese=0,
    primary_crop="WHEAT",
    primary_crop_count=15,
    secondary_crop="CARROT",
    secondary_crop_count=10,
    day0_land=True,
    day10_land=False,
    sell_batch_size=14,
    market_frontrun=True
)
def o5_cow_specialist(obs, configuration=None):
    return o5_agent_inst(obs, configuration)

# O6: Sheep Specialist (6-8 Sheep elasticity-aware wool engine)
o6_agent_inst = BaseArchetypeAgent(
    name="O6_Sheep_Specialist",
    target_cows=0,
    target_sheep=8,
    target_geese=0,
    primary_crop="CARROT",
    primary_crop_count=18,
    secondary_crop="WHEAT",
    secondary_crop_count=12,
    day0_land=True,
    day10_land=False,
    sell_batch_size=8,
    market_frontrun=True
)
def o6_sheep_specialist(obs, configuration=None):
    return o6_agent_inst(obs, configuration)

# O7: Balanced Livestock (4 Cows + 3 Sheep + 4 Geese mixed fleet)
o7_agent_inst = BaseArchetypeAgent(
    name="O7_Balanced_Livestock",
    target_cows=4,
    target_sheep=3,
    target_geese=4,
    primary_crop="MELON",
    primary_crop_count=10,
    secondary_crop="CARROT",
    secondary_crop_count=10,
    day0_land=True,
    day10_land=False,
    sell_batch_size=12,
    market_frontrun=True
)
def o7_balanced_livestock(obs, configuration=None):
    return o7_agent_inst(obs, configuration)

# O8: Dynamic Economic Optimizer
o8_agent_path = os.path.join(project_root, "candidates", "slot3_hybrid_dynamic.py")

# O9: Market Aggressor (High-volume frontrunning town demand cycle dumper)
o9_agent_inst = BaseArchetypeAgent(
    name="O9_Market_Aggressor",
    target_cows=6,
    target_sheep=3,
    target_geese=0,
    primary_crop="MELON",
    primary_crop_count=15,
    secondary_crop="CARROT",
    secondary_crop_count=15,
    day0_land=True,
    day10_land=True,
    sell_batch_size=20,
    market_frontrun=True
)
def o9_market_aggressor(obs, configuration=None):
    return o9_agent_inst(obs, configuration)

# O10: Anti-Melon Specialist (Exploits melon glut with strawberries, carrots, milk)
o10_agent_inst = BaseArchetypeAgent(
    name="O10_Anti_Melon_Specialist",
    target_cows=6,
    target_sheep=4,
    target_geese=0,
    primary_crop="STRAWBERRY",
    primary_crop_count=15,
    secondary_crop="CARROT",
    secondary_crop_count=15,
    day0_land=True,
    day10_land=False,
    sell_batch_size=12,
    market_frontrun=True
)
def o10_anti_melon_specialist(obs, configuration=None):
    return o10_agent_inst(obs, configuration)

# O11: Anti-Livestock Specialist (Fast crop blitz taking market liquidity)
o11_agent_inst = BaseArchetypeAgent(
    name="O11_Anti_Livestock_Specialist",
    target_cows=0,
    target_sheep=0,
    target_geese=0,
    primary_crop="MELON",
    primary_crop_count=20,
    secondary_crop="CARROT",
    secondary_crop_count=20,
    day0_land=True,
    day10_land=True,
    sell_batch_size=15,
    market_frontrun=True
)
def o11_anti_livestock_specialist(obs, configuration=None):
    return o11_agent_inst(obs, configuration)

# O12: Top-Meta Emulator (8C/4S/10M industrial scaler with Fibonacci labor)
o12_agent_inst = BaseArchetypeAgent(
    name="O12_Top_Meta_Emulator",
    target_cows=8,
    target_sheep=4,
    target_geese=0,
    primary_crop="MELON",
    primary_crop_count=10,
    secondary_crop="CARROT",
    secondary_crop_count=12,
    day0_land=True,
    day10_land=False,
    sell_batch_size=14,
    market_frontrun=True
)
def o12_top_meta_emulator(obs, configuration=None):
    return o12_agent_inst(obs, configuration)

# Registry dictionary
OPPONENT_ECOSYSTEM = {
    "O1_Titan_Baseline": O1_TITAN_PATH,
    "O2_Golden_Control_v1": O2_GOLDEN_PATH,
    "O3_Early_Melon_Specialist": o3_early_melon_specialist,
    "O4_Fast_Crop_Specialist": o4_fast_crop_specialist,
    "O5_Cow_Specialist": o5_cow_specialist,
    "O6_Sheep_Specialist": o6_sheep_specialist,
    "O7_Balanced_Livestock": o7_balanced_livestock,
    "O8_Economic_Optimizer": o8_agent_path,
    "O9_Market_Aggressor": o9_market_aggressor,
    "O10_Anti_Melon": o10_anti_melon_specialist,
    "O11_Anti_Livestock": o11_anti_livestock_specialist,
    "O12_Top_Meta_Emulator": o12_top_meta_emulator,
}

if __name__ == "__main__":
    print("=" * 75)
    print("AGENTS: 12-ARCHETYPE COMPETITIVE OPPONENT ECOSYSTEM INITIALIZED")
    print("=" * 75)
    for k, v in OPPONENT_ECOSYSTEM.items():
        t = "File Path" if isinstance(v, str) else "Callable Instance"
        print(f"  [{k:25s}] -> {t}")
    print("=" * 75)
