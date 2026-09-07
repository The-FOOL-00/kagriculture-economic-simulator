import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

BOARD_SIZE = 10
TURNS_PER_DAY = 24
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield": 2, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield": 2, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield": 8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield": 10, "max_yield": 6, "ongoing": False},
}

# Designated Pastures in NW Quadrant
PASTURE_TILES = [(3, 3), (4, 3), (3, 4), (4, 2)]

# Crop tiles in NW Quadrant (19 tiles)
# 12 Melons:
MELON_TILES = [
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
    (0, 2), (1, 2)
]
# 7 Wheat:
WHEAT_TILES = [
    (2, 2), (3, 2), (0, 3), (1, 3), (2, 3), (0, 4), (1, 4)
]

MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def bfs_step(start, target, tiles):
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target

    dx, dy = tx - sx, ty - sy
    if abs(dx) + abs(dy) == 1:
        for m_name, (mx, my) in MOVES.items():
            if mx == dx and my == dy:
                return m_name

    queue = [start]
    visited = {start: None}
    head = 0
    while head < len(queue):
        cx, cy = queue[head]
        head += 1
        if (cx, cy) == target:
            break
        for m_name, (mx, my) in MOVES.items():
            nx, ny = cx + mx, cy + my
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if (nx, ny) not in visited:
                    visited[(nx, ny)] = ((cx, cy), m_name)
                    queue.append((nx, ny))

    if target not in visited or visited[target] is None:
        best_m = "PASS"
        best_dist = 999
        for m_name, (mx, my) in MOVES.items():
            nx, ny = sx + mx, sy + my
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                d = manhattan((nx, ny), target)
                if d < best_dist:
                    best_dist = d
                    best_m = m_name
        return best_m

    curr = target
    first_move = "PASS"
    while visited[curr] is not None:
        prev, move = visited[curr]
        if prev == start:
            first_move = move
            break
        curr = prev
    return first_move


class ClosedLoopCoreAgent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.q2_bought = False
        self.q3_bought = False

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", [{}, {}]) or [{}, {}]
        farm = farms[player] if len(farms) > player else {}
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        seeds = dict(private.get("seeds", {}) or {})
        inventories = list(private.get("inventories", []) or [])

        tiles = farm.get("tiles", []) or []
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        hands_pos = [tuple(p) for p in farm.get("hands", []) or []]
        all_workers = [farmer_pos] + hands_pos
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]

        day = step // TURNS_PER_DAY
        hour = step % TURNS_PER_DAY

        # =====================================================================
        # 1. MARKET LAYER (Observation Driven)
        # =====================================================================
        market_orders = []

        if step == 0:
            # Day 0 Opening: 3 Cows, 1 Sheep, 7 Melon, 10 Wheat, 17 Wheat Feed, 2 Hands
            market_orders = [
                ["BUY_ANIMAL", "COW", 3],
                ["BUY_ANIMAL", "SHEEP", 1],
                ["BUY_SEED", "MELON", 7],
                ["BUY_SEED", "WHEAT", 10],
                ["BUY_PRODUCT", "WHEAT", 17],
                ["HIRE"],
                ["HIRE"]
            ]
        elif hour == 0:
            # Daily morning routine:
            # Liquidate fertilizer
            fert_held = int(shed.get("FERTILIZER", 0) or 0)
            if fert_held > 0:
                market_orders.append(["SELL", "FERTILIZER", fert_held])

            # Liquidate milk & wool
            milk_held = int(shed.get("MILK", 0) or 0)
            if milk_held > 0:
                market_orders.append(["SELL", "MILK", milk_held])
            wool_held = int(shed.get("WOOL", 0) or 0)
            if wool_held > 0:
                market_orders.append(["SELL", "WOOL", wool_held])

            # Liquidate melons
            melon_held = int(shed.get("MELON", 0) or 0)
            if melon_held > 0:
                market_orders.append(["SELL", "MELON", melon_held])

            # Liquidate strawberries
            straw_held = int(shed.get("STRAWBERRY", 0) or 0)
            if straw_held > 0:
                market_orders.append(["SELL", "STRAWBERRY", straw_held])

            # Buy Land Q2 (NE) if money >= 1000 and day >= 7
            if len(quads) == 1 and money >= 1000 and day >= 6 and not self.q2_bought:
                market_orders.append(["BUY_LAND"])
                self.q2_bought = True

            # Buy Land Q3 (SW) if money >= 2000 and day >= 11 and not self.q3_bought:
            if len(quads) == 2 and money >= 2000 and day >= 10 and not self.q3_bought:
                market_orders.append(["BUY_LAND"])
                self.q3_bought = True

            # Feed replenishment: keep at least 8 feed in shed
            wheat_held = int(shed.get("WHEAT", 0) or 0)
            if wheat_held < 8 and money >= 200:
                market_orders.append(["BUY_PRODUCT", "WHEAT", min(10, int(money // 30))])

            # Replant seeds
            if day >= 10 and money >= 500:
                if int(seeds.get("MELON", 0) or 0) < 7:
                    market_orders.append(["BUY_SEED", "MELON", 7])
                if len(quads) >= 2 and int(seeds.get("STRAWBERRY", 0) or 0) < 10:
                    market_orders.append(["BUY_SEED", "STRAWBERRY", 5])

            # Labor hiring: 2 hands early game, 4-8 hands mid/late game
            hires_today = int(farm.get("hires_today", 0) or 0)
            if day < 7:
                target_hands = 2
            elif day < 11:
                target_hands = 4 if money >= 500 else 2
            else:
                target_hands = 6 if money >= 1500 else 3

            can_hire = min(10 - len(market_orders), max(0, target_hands - hires_today))
            for _ in range(can_hire):
                market_orders.append(["HIRE"])

        # =====================================================================
        # 2. WORKER LAYER (Farmer: Livestock & Shed Logistics)
        # =====================================================================
        farmer_act = ["PASS"]
        hands_act = [["PASS"] for _ in hands_pos]

        fx, fy = farmer_pos
        f_inv = inventories[0] if len(inventories) > 0 else {}
        f_tile = tiles[fy][fx] if 0 <= fy < BOARD_SIZE and 0 <= fx < BOARD_SIZE else None
        f_load = sum(f_inv.values())

        # Check livestock state
        hungry_pastures = []
        fert_pastures = []
        empty_pastures = []
        yield_pastures = []
        unbuilt_pastures = []

        for p in PASTURE_TILES:
            px, py = p
            t = tiles[py][px]
            if t is None:
                unbuilt_pastures.append(p)
            elif isinstance(t, dict):
                if t.get("kind") == "PASTURE":
                    if not t.get("animal"):
                        empty_pastures.append(p)
                    else:
                        if not t.get("fed_today"):
                            hungry_pastures.append(p)
                        if t.get("fertilizer_available"):
                            fert_pastures.append(p)
                        if int(t.get("yield_units", 0) or 0) > 0:
                            yield_pastures.append(p)

        # Farmer Decision Tree:
        # A. Current tile actions
        if f_tile is None and farmer_pos in PASTURE_TILES:
            farmer_act = ["BUILD_PASTURE"]
        elif isinstance(f_tile, dict) and f_tile.get("kind") == "PASTURE":
            if not f_tile.get("animal"):
                if f_inv.get("COW", 0) > 0:
                    farmer_act = ["PLACE", "COW"]
                elif f_inv.get("SHEEP", 0) > 0:
                    farmer_act = ["PLACE", "SHEEP"]
            else:
                if not f_tile.get("fed_today") and f_inv.get("WHEAT", 0) > 0:
                    farmer_act = ["FEED"]
                elif f_tile.get("fertilizer_available"):
                    farmer_act = ["COLLECT_FERTILIZER"]
                elif int(f_tile.get("yield_units", 0) or 0) > 0:
                    farmer_act = ["HARVEST"]
        elif farmer_pos in [(4, 4), (5, 4), (4, 5), (5, 5)]:
            # Standing at shed
            has_drops = any(k in ("FERTILIZER", "MILK", "WOOL", "MELON", "STRAWBERRY", "WHEAT") for k, v in f_inv.items() if v > 0)
            if has_drops:
                farmer_act = ["DROP"]
            elif empty_pastures and f_load == 0:
                if shed.get("COW", 0) > 0:
                    farmer_act = ["PICKUP", "COW", 1]
                elif shed.get("SHEEP", 0) > 0:
                    farmer_act = ["PICKUP", "SHEEP", 1]
            elif hungry_pastures and f_inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
                farmer_act = ["PICKUP", "WHEAT", min(4, shed.get("WHEAT", 0))]

        # B. Movement if no action taken on current tile
        if farmer_act == ["PASS"]:
            target = None
            if unbuilt_pastures:
                target = unbuilt_pastures[0]
            elif f_inv.get("COW", 0) > 0 or f_inv.get("SHEEP", 0) > 0:
                target = empty_pastures[0] if empty_pastures else (4, 4)
            elif empty_pastures and (shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0) and f_load == 0:
                target = (4, 4)
            elif hungry_pastures:
                if f_inv.get("WHEAT", 0) > 0:
                    target = hungry_pastures[0]
                elif shed.get("WHEAT", 0) > 0:
                    target = (4, 4)
            elif fert_pastures:
                target = fert_pastures[0]
            elif yield_pastures:
                target = yield_pastures[0]
            elif f_load > 0:
                target = (4, 4)

            if target and target != farmer_pos:
                farmer_act = [bfs_step(farmer_pos, target, tiles)]

        # =====================================================================
        # 3. FIELD WORKERS (Hands: Crop Tending)
        # =====================================================================
        # Identify all crop chores
        unwatered_crops = []
        ripe_crops = []
        unplanted_tiles = []

        all_target_crops = MELON_TILES + WHEAT_TILES
        for cp in all_target_crops:
            cx, cy = cp
            ct = tiles[cy][cx]
            if ct is None:
                unplanted_tiles.append(cp)
            elif isinstance(ct, dict) and ct.get("kind") == "PLANT":
                crop_name = ct.get("crop")
                age = day - int(ct.get("planted_day", 0) or 0)
                first_y = CROPS.get(crop_name, {}).get("first_yield", 2)
                if age >= first_y and int(ct.get("yield_units", 0) or 0) > 0:
                    ripe_crops.append(cp)
                elif not ct.get("watered_today"):
                    unwatered_crops.append(cp)

        for h_idx, h_pos in enumerate(hands_pos):
            hx, hy = h_pos
            w_idx = h_idx + 1
            h_inv = inventories[w_idx] if w_idx < len(inventories) else {}
            h_load = sum(h_inv.values())
            h_tile = tiles[hy][hx] if 0 <= hy < BOARD_SIZE and 0 <= hx < BOARD_SIZE else None

            # Action on current tile
            h_act = ["PASS"]
            if h_pos in [(4, 4), (5, 4), (4, 5), (5, 5)] and h_load > 0:
                h_act = ["DROP"]
            elif isinstance(h_tile, dict) and h_tile.get("kind") == "PLANT":
                crop_name = h_tile.get("crop")
                age = day - int(h_tile.get("planted_day", 0) or 0)
                first_y = CROPS.get(crop_name, {}).get("first_yield", 2)
                if age >= first_y and int(h_tile.get("yield_units", 0) or 0) > 0:
                    h_act = ["HARVEST"]
                elif not h_tile.get("watered_today"):
                    h_act = ["WATER"]
            elif h_tile is None and h_pos in all_target_crops:
                if h_pos in MELON_TILES and seeds.get("MELON", 0) > 0:
                    h_act = ["PLANT", "MELON"]
                    seeds["MELON"] -= 1
                elif seeds.get("WHEAT", 0) > 0:
                    h_act = ["PLANT", "WHEAT"]
                    seeds["WHEAT"] -= 1

            # Movement if PASS
            if h_act == ["PASS"]:
                h_target = None
                if h_load >= 3:
                    h_target = (4, 4)
                elif unplanted_tiles:
                    # Pick closest unplanted tile
                    h_target = min(unplanted_tiles, key=lambda t: manhattan(h_pos, t))
                elif unwatered_crops:
                    h_target = min(unwatered_crops, key=lambda t: manhattan(h_pos, t))
                elif ripe_crops:
                    h_target = min(ripe_crops, key=lambda t: manhattan(h_pos, t))
                elif h_load > 0:
                    h_target = (4, 4)

                if h_target and h_target != h_pos:
                    h_act = [bfs_step(h_pos, h_target, tiles)]

            hands_act[h_idx] = h_act

        return {
            "farmer": farmer_act,
            "hands": hands_act,
            "market": market_orders[:10]
        }

if __name__ == "__main__":
    cl = ClosedLoopCoreAgent()
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        obs0 = env.state[0].observation
        act0 = cl(obs0)
        act1 = v2.agent(env.state[1].observation)
        env.step([act0, act1])
        if s in (23, 119, 239, 359, 479, 599, 718):
            f0 = env.state[0].observation["farms"][0]
            f1 = env.state[1].observation["farms"][1]
            print(f"Step {s:3d} (D{s//24:2d} H{s%24:2d}) | CL Cash=${f0['money']:8.1f} Hands={len(f0['hands'])} | V2 Cash=${f1['money']:8.1f}")
            
    print(f"\nFinal Reward: CL=${env.steps[-1][0]['reward']:,.1f} | V2=${env.steps[-1][1]['reward']:,.1f}")
