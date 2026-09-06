"""
scratch/closed_loop_arch_v1.py
Clean, 100% Closed-Loop Synchronized Spatial/Capital/Livestock Agent for Kaggriculture.
Zero hardcoded action replay tapes.
Zero per-step trace lookup.
All decisions generated from current online observation (obs).
"""

import math
import copy
from collections import deque

BOARD_SIZE = 10
TURNS_PER_DAY = 24
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

OPPOSITE_MOVES = {
    (0, -1): "NORTH",
    (0, 1):  "SOUTH",
    (1, 0):  "EAST",
    (-1, 0): "WEST",
}

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "ongoing": False},
}

# Optimal Shed-Clustered 16-Pasture Layout (5 in NW, 8 in NE, 3 in SW)
PASTURE_TARGETS = {
    "NW": [(4, 4), (4, 3), (3, 4), (3, 3), (4, 2)],
    "SW": [(4, 5), (3, 5), (4, 6)],
    "NE": [(5, 4), (5, 3), (5, 2), (6, 4), (6, 3), (7, 4), (7, 3), (9, 4)],
}
ALL_PASTURE_TILES = set(PASTURE_TARGETS["NW"] + PASTURE_TARGETS["NE"] + PASTURE_TARGETS["SW"])

BASE_PRICES = {
    "MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200, 
    "FERTILIZER": 100, "TOMATO": 60, "EGG": 50, "CARROT": 35, "WHEAT": 25
}


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_unlocked_shed_tiles(tiles):
    valid = []
    for x, y in SHED_TILES:
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if tiles[y][x] != "LOCKED":
                valid.append((x, y))
    return valid if valid else [(4, 4)]


def bfs_distance_map(start, tiles):
    sx, sy = start
    dist = {start: 0}
    parent = {start: None}
    queue = deque([start])

    while queue:
        cx, cy = queue.popleft()
        for d_name, (dx, dy) in FARMER_MOVES.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if (nx, ny) not in dist and tiles[ny][nx] != "LOCKED":
                    dist[(nx, ny)] = dist[(cx, cy)] + 1
                    parent[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny))
    return dist, parent


def get_next_step(start, target, tiles):
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target

    dx = tx - sx
    dy = ty - sy
    if abs(dx) + abs(dy) == 1:
        move = OPPOSITE_MOVES.get((dx, dy))
        if move and 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE and tiles[ty][tx] != "LOCKED":
            return move

    dist, parent = bfs_distance_map(target, tiles)
    if start not in dist:
        for move, (mdx, mdy) in FARMER_MOVES.items():
            nx, ny = sx + mdx, sy + mdy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and tiles[ny][nx] != "LOCKED":
                if manhattan((nx, ny), target) < manhattan(start, target):
                    return move
        return "PASS"

    best_move = "PASS"
    min_d = 999999
    for move, (mdx, mdy) in FARMER_MOVES.items():
        nx, ny = sx + mdx, sy + mdy
        pos = (nx, ny)
        if pos in dist and dist[pos] < min_d:
            min_d = dist[pos]
            best_move = move

    return best_move


class ClosedLoopArchAgent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.q2_unlocked = False
        self.q3_unlocked = False

    def __call__(self, obs, config=None):
        step = min(int(obs.get("step", 0) or 0), 719)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        my_farm = farms[player] if len(farms) > player else {}
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        seeds = private.get("seeds") or {}
        inventories = private.get("inventories") or [{}]
        market_info = obs.get("market") or {}
        market_prices = market_info.get("prices") or BASE_PRICES
        unlocked_quads = set(my_farm.get("unlocked_quadrants") or ["NW"])

        money = float(my_farm.get("money", 0) or 0)
        tiles = my_farm.get("tiles") or [[None]*10 for _ in range(10)]
        farmer_pos = tuple(my_farm.get("farmer") or [4, 4])
        hands_pos = [tuple(h) for h in (my_farm.get("hands") or [])]
        all_workers = [farmer_pos] + hands_pos

        day = step // TURNS_PER_DAY
        hour = step % TURNS_PER_DAY

        if "NE" in unlocked_quads: self.q2_unlocked = True
        if "SW" in unlocked_quads: self.q3_unlocked = True

        # Scan Farm Tiles
        built_pastures = []
        cows_placed = []
        sheep_placed = []
        empty_pastures = []
        unwatered_crops = []
        ripe_crops = []
        weed_tiles = []
        empty_soil_tiles = []
        fertilizer_ready = []
        unfed_animals = []
        uncared_animals = []
        ripe_animals = []

        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                t = tiles[y][x]
                pos = (x, y)
                if t == "LOCKED":
                    continue
                if t is None:
                    if pos not in ALL_PASTURE_TILES:
                        empty_soil_tiles.append(pos)
                elif isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "PASTURE":
                        built_pastures.append(pos)
                        animal = t.get("animal")
                        if animal == "COW":
                            cows_placed.append(pos)
                        elif animal == "SHEEP":
                            sheep_placed.append(pos)
                        else:
                            empty_pastures.append(pos)
                        
                        if animal:
                            if t.get("fertilizer_available"):
                                fertilizer_ready.append(pos)
                            if not t.get("fed_today"):
                                unfed_animals.append(pos)
                            if not t.get("cared_today"):
                                uncared_animals.append(pos)
                            if t.get("yield_units", 0) > 0:
                                ripe_animals.append(pos)
                    elif kind == "PLANT":
                        crop = t.get("crop")
                        age = day - t.get("planted_day", day)
                        first_yield = CROPS.get(crop, {}).get("first_yield_day", 2)
                        
                        if age >= first_yield and t.get("yield_units", 0) > 0:
                            ripe_crops.append(pos)
                        elif not t.get("watered_today"):
                            unwatered_crops.append(pos)
                    elif kind == "WEED":
                        weed_tiles.append(pos)

        # -------------------------------------------------------------
        # 1. CAPITAL & LABOR SIZING
        # -------------------------------------------------------------
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
        if day <= 4:
            target_hands = 2 # 3 workers total
        elif day <= 9:
            target_hands = 4 if self.q2_unlocked else 2 # 5 workers total
        elif day <= 15:
            target_hands = 7 if self.q3_unlocked else (4 if self.q2_unlocked else 2) # 8 workers total
        else:
            target_hands = 11 if self.q3_unlocked else (7 if self.q2_unlocked else 2) # 12 workers total

        hire_cost = sum(fib[i] for i in range(target_hands))
        while target_hands > 1 and sum(fib[i] for i in range(target_hands)) > max(0, money - 50):
            target_hands -= 1
        hire_cost = sum(fib[i] for i in range(target_hands))

        held_milk_qty = int(shed.get("MILK", 0) or 0)
        milk_val = held_milk_qty * market_prices.get("MILK", 160)
        shed_wheat_qty = int(shed.get("WHEAT", 0) or 0)
        fert_qty = int(shed.get("FERTILIZER", 0) or 0)

        should_unlock_q2 = False
        should_unlock_q3 = False

        if not self.q2_unlocked:
            if day >= 4 and (money + shed_wheat_qty * 25 + fert_qty * 100 >= 1000):
                should_unlock_q2 = True
        elif not self.q3_unlocked:
            if day >= 6 and (money + milk_val + fert_qty * 100 >= 2000):
                should_unlock_q3 = True

        reserved_wages = hire_cost if hour == 0 else 0
        reserved_land = 1000 if (should_unlock_q2 and "NE" not in unlocked_quads) else (2000 if (should_unlock_q3 and "SW" not in unlocked_quads) else 0)
        discretionary_cash = max(0.0, money - reserved_wages - reserved_land)

        # -------------------------------------------------------------
        # 2. MARKET CONTROLLER
        # -------------------------------------------------------------
        market_orders = []

        # A. MANDATORY UNLOCKS (Top of queue)
        if should_unlock_q2 and "NE" not in unlocked_quads:
            if money < 1000:
                if fert_qty > 0:
                    market_orders.append(["SELL", "FERTILIZER", fert_qty])
                if shed_wheat_qty > 0:
                    market_orders.append(["SELL", "WHEAT", min(35, shed_wheat_qty)])
            market_orders.append(["BUY_LAND"])

        elif should_unlock_q3 and "SW" not in unlocked_quads:
            if held_milk_qty > 0:
                market_orders.append(["SELL", "MILK", min(6, held_milk_qty)])
            if fert_qty > 0:
                market_orders.append(["SELL", "FERTILIZER", fert_qty])
            market_orders.append(["BUY_LAND"])

        # B. MORNING COMMODITY SALES
        if hour <= 2:
            if fert_qty > 0 and not should_unlock_q3:
                market_orders.append(["SELL", "FERTILIZER", fert_qty])
            if int(shed.get("MELON", 0) or 0) > 0:
                market_orders.append(["SELL", "MELON", int(shed.get("MELON", 0))])
            if int(shed.get("STRAWBERRY", 0) or 0) > 0:
                market_orders.append(["SELL", "STRAWBERRY", int(shed.get("STRAWBERRY", 0))])
            if int(shed.get("WOOL", 0) or 0) > 0:
                market_orders.append(["SELL", "WOOL", int(shed.get("WOOL", 0))])
            if self.q3_unlocked and int(shed.get("MILK", 0) or 0) > 0:
                market_orders.append(["SELL", "MILK", int(shed.get("MILK", 0))])

        # C. LABOR HIRES (Hour 0)
        if hour == 0 and step > 0:
            needed_hires = max(0, target_hands - my_farm.get("hires_today", 0))
            for _ in range(needed_hires):
                market_orders.append(["HIRE"])

        # D. DAY 0 INITIAL SETUP
        if step == 0:
            market_orders = [
                ["BUY_ANIMAL", "COW", 3],
                ["BUY_ANIMAL", "SHEEP", 1],
                ["BUY_SEED", "MELON", 7],
                ["BUY_SEED", "WHEAT", 10],
                ["BUY_PRODUCT", "WHEAT", 17],
                ["HIRE"],
                ["HIRE"]
            ]

        # E. LIVESTOCK PURCHASES (Scale herd to capacity)
        if step > 0 and len(market_orders) < 8:
            unplaced_cows = int(shed.get("COW", 0) or 0)
            total_cows = len(cows_placed) + unplaced_cows
            
            if total_cows < len(built_pastures) and unplaced_cows == 0:
                if len(cows_placed) < 13 and discretionary_cash >= 600:
                    market_orders.append(["BUY_ANIMAL", "COW", 1])
                    discretionary_cash -= 600

        # F. FEED BUFFER
        total_herd = len(cows_placed) + len(sheep_placed)
        if step > 0 and total_herd > 0 and shed_wheat_qty < 12 and len(market_orders) < 8:
            buy_qty = min(20, 25 - shed_wheat_qty)
            if money >= buy_qty * 25 + 50:
                market_orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                discretionary_cash = max(0.0, discretionary_cash - buy_qty * 25)

        # G. SEED PURCHASES (High-Margin Cash Crops)
        if 24 < step < 650 and len(market_orders) < 9 and len(empty_soil_tiles) > 0:
            total_seeds = sum(seeds.values())
            if total_seeds < len(empty_soil_tiles) and discretionary_cash >= 150:
                if self.q3_unlocked:
                    if discretionary_cash >= 500:
                        market_orders.append(["BUY_SEED", "STRAWBERRY", 5])
                        discretionary_cash -= 500
                    elif discretionary_cash >= 400:
                        market_orders.append(["BUY_SEED", "MELON", 5])
                        discretionary_cash -= 400
                    elif discretionary_cash >= 250:
                        market_orders.append(["BUY_SEED", "TOMATO", 5])
                        discretionary_cash -= 250
                elif self.q2_unlocked:
                    if discretionary_cash >= 400:
                        market_orders.append(["BUY_SEED", "MELON", 5])
                        discretionary_cash -= 400
                    elif discretionary_cash >= 500:
                        market_orders.append(["BUY_SEED", "STRAWBERRY", 5])
                        discretionary_cash -= 500
                else:
                    if discretionary_cash >= 100:
                        market_orders.append(["BUY_SEED", "WHEAT", 5])
                        discretionary_cash -= 50

        # H. GENERAL COMMODITY SELLS
        if step >= 712:
            for item in ("MELON", "STRAWBERRY", "WOOL", "MILK", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"):
                qty = int(shed.get(item, 0) or 0)
                if qty > 0 and len(market_orders) < 10:
                    market_orders.append(["SELL", item, qty])

        # -------------------------------------------------------------
        # 3. WORKER CHORE ALLOCATION & PATHFINDING
        # -------------------------------------------------------------
        unlocked_shed_tiles = get_unlocked_shed_tiles(tiles)
        farmer_action = ["PASS"]
        hands_actions = [["PASS"] for _ in range(len(hands_pos))]

        unbuilt_pasture_targets = []
        for quad in ["NW", "NE", "SW"]:
            if quad in unlocked_quads:
                for pos in PASTURE_TARGETS[quad]:
                    if tiles[pos[1]][pos[0]] is None:
                        unbuilt_pasture_targets.append(pos)

        chores = []
        # Priority 1: Harvests (Max Priority at terminal)
        harvest_weight = 200 if step >= 710 else 100
        for pos in ripe_crops:
            chores.append({"type": "HARVEST_PLANT", "pos": pos, "weight": harvest_weight})
        for pos in ripe_animals:
            chores.append({"type": "HARVEST_ANIMAL", "pos": pos, "weight": harvest_weight - 2})

        # Priority 2: Hungry animal feeding (life critical)
        for pos in unfed_animals:
            chores.append({"type": "FEED_ANIMAL", "pos": pos, "weight": 98})

        # Priority 3: Plant care (WATERING IS TOP PRIORITY TO PREVENT ROT AND MAX YIELD!)
        for pos in unwatered_crops:
            chores.append({"type": "WATER_PLANT", "pos": pos, "weight": 96})

        # Priority 4: Place animals into empty pastures immediately
        unplaced_cows = int(shed.get("COW", 0) or 0)
        unplaced_sheep = int(shed.get("SHEEP", 0) or 0)
        if (unplaced_cows > 0 or unplaced_sheep > 0) and len(empty_pastures) > 0:
            for p_pos in empty_pastures:
                animal_type = "COW" if unplaced_cows > 0 else "SHEEP"
                chores.append({"type": "PLACE_ANIMAL", "pos": p_pos, "animal": animal_type, "weight": 92})

        # Priority 5: Seed planting
        if step < 650:
            available_seeds = dict(seeds)
            for pos in empty_soil_tiles:
                chosen_seed = None
                if available_seeds.get("STRAWBERRY", 0) > 0: chosen_seed = "STRAWBERRY"
                elif available_seeds.get("MELON", 0) > 0: chosen_seed = "MELON"
                elif available_seeds.get("TOMATO", 0) > 0: chosen_seed = "TOMATO"
                elif available_seeds.get("WHEAT", 0) > 0: chosen_seed = "WHEAT"
                elif available_seeds.get("CARROT", 0) > 0: chosen_seed = "CARROT"
                
                if chosen_seed:
                    chores.append({"type": "PLANT_SEED", "pos": pos, "crop": chosen_seed, "weight": 85})

        # Priority 6: Collect Fertilizer
        for pos in fertilizer_ready:
            chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 80})

        # Priority 7: Build Pastures
        for p_pos in unbuilt_pasture_targets:
            chores.append({"type": "BUILD_PASTURE", "pos": p_pos, "weight": 75})

        # Priority 8: Animal Care (mood)
        for pos in uncared_animals:
            chores.append({"type": "CARE_ANIMAL", "pos": pos, "weight": 65})

        # Priority 9: Clear Weeds
        for pos in weed_tiles:
            chores.append({"type": "DIG_WEED", "pos": pos, "weight": 60})

        assigned_chores = set()

        for w_idx, w_pos in enumerate(all_workers):
            w_inv = inventories[w_idx] if w_idx < len(inventories) else {}
            carrying_items = sum(w_inv.values())

            # Unload commodities at shed
            has_unloadable = any(k in ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "EGG", "MILK", "WOOL", "FERTILIZER") for k in w_inv)
            if not has_unloadable and "WHEAT" in w_inv and len(unfed_animals) == 0 and carrying_items >= 2:
                has_unloadable = True

            if has_unloadable and (carrying_items >= 1 or len(ripe_crops) == 0 or step >= 710):
                nearest_shed = min(unlocked_shed_tiles, key=lambda s: manhattan(w_pos, s))
                if w_pos == nearest_shed:
                    act = ["DROP"]
                else:
                    move = get_next_step(w_pos, nearest_shed, tiles)
                    act = [move]
                
                if w_idx == 0: farmer_action = act
                else: hands_actions[w_idx - 1] = act
                continue

            best_chore = None
            best_score = -999999

            for c_idx, chore in enumerate(chores):
                if c_idx in assigned_chores:
                    continue
                dist = manhattan(w_pos, chore["pos"])
                score = chore["weight"] * 10 - dist * 3
                if score > best_score:
                    best_score = score
                    best_chore = (c_idx, chore)

            if best_chore is None:
                act = ["PASS"]
                if w_idx == 0: farmer_action = act
                else: hands_actions[w_idx - 1] = act
                continue

            c_idx, chore = best_chore
            assigned_chores.add(c_idx)
            c_type = chore["type"]
            c_pos = chore["pos"]

            if w_pos == c_pos:
                if c_type == "HARVEST_PLANT" or c_type == "HARVEST_ANIMAL":
                    act = ["HARVEST"]
                elif c_type == "COLLECT_FERTILIZER":
                    act = ["COLLECT_FERTILIZER"]
                elif c_type == "FEED_ANIMAL":
                    if w_inv.get("WHEAT", 0) > 0:
                        act = ["FEED"]
                    elif int(shed.get("WHEAT", 0) or 0) > 0:
                        nearest_shed = min(unlocked_shed_tiles, key=lambda s: manhattan(w_pos, s))
                        move = get_next_step(w_pos, nearest_shed, tiles)
                        act = [move]
                    else:
                        act = ["CARE"]
                elif c_type == "CARE_ANIMAL":
                    act = ["CARE"]
                elif c_type == "BUILD_PASTURE":
                    act = ["BUILD_PASTURE"]
                elif c_type == "DIG_WEED":
                    act = ["DIG"]
                elif c_type == "WATER_PLANT":
                    act = ["WATER"]
                elif c_type == "PLANT_SEED":
                    crop = chore["crop"]
                    act = ["PLANT", crop]
                    available_seeds[crop] = max(0, available_seeds.get(crop, 0) - 1)
                elif c_type == "PLACE_ANIMAL":
                    animal = chore.get("animal", "COW")
                    if w_inv.get(animal, 0) > 0:
                        act = ["PLACE", animal]
                    else:
                        nearest_shed = min(unlocked_shed_tiles, key=lambda s: manhattan(w_pos, s))
                        move = get_next_step(w_pos, nearest_shed, tiles)
                        act = [move]
                else:
                    act = ["PASS"]
            else:
                if c_type == "PLACE_ANIMAL":
                    animal = chore.get("animal", "COW")
                    if w_inv.get(animal, 0) == 0:
                        nearest_shed = min(unlocked_shed_tiles, key=lambda s: manhattan(w_pos, s))
                        if w_pos == nearest_shed:
                            act = ["PICKUP", animal, 1]
                        else:
                            move = get_next_step(w_pos, nearest_shed, tiles)
                            act = [move]
                        if w_idx == 0: farmer_action = act
                        else: hands_actions[w_idx - 1] = act
                        continue
                elif c_type == "FEED_ANIMAL":
                    if w_inv.get("WHEAT", 0) == 0 and int(shed.get("WHEAT", 0) or 0) > 0:
                        nearest_shed = min(unlocked_shed_tiles, key=lambda s: manhattan(w_pos, s))
                        if w_pos == nearest_shed:
                            act = ["PICKUP", "WHEAT", 1]
                        else:
                            move = get_next_step(w_pos, nearest_shed, tiles)
                            act = [move]
                        if w_idx == 0: farmer_action = act
                        else: hands_actions[w_idx - 1] = act
                        continue

                move = get_next_step(w_pos, c_pos, tiles)
                act = [move]

            if w_idx == 0:
                farmer_action = act
            else:
                hands_actions[w_idx - 1] = act

        if step == 0:
            farmer_action = ["BUILD_PASTURE"]
            hands_actions = []

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders[:10]
        }


_agent_inst = ClosedLoopArchAgent()

def agent(obs, config=None):
    return _agent_inst(obs, config)
