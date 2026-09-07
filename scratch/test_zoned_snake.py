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

# Farmer Zone: Pastures around shed
PASTURE_NW = [(3, 3), (4, 3), (3, 4), (4, 2)]

# Dedicated Row Paths for Field Hands
ROW0_PATH = [(4, 0), (3, 0), (2, 0), (1, 0), (0, 0)]
ROW1_PATH = [(4, 1), (3, 1), (2, 1), (1, 1), (0, 1)]
ROW2_PATH = [(3, 2), (2, 2), (1, 2), (0, 2)]
ROW34_PATH = [(0, 3), (1, 3), (2, 3), (2, 4), (1, 4), (0, 4)]

NORTH_PATH = ROW0_PATH + ROW1_PATH
SOUTH_PATH = ROW2_PATH + ROW34_PATH

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


class ZonedSnakeAgent:
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
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]

        day = step // TURNS_PER_DAY
        hour = step % TURNS_PER_DAY

        # =====================================================================
        # 1. MARKET LAYER
        # =====================================================================
        market_orders = []

        if step == 0:
            # JIT Opening: 2 Cows, 2 Sheep, 12 Melons, 7 Wheat, 4 Wheat Feed, 4 Hands
            market_orders = [
                ["BUY_ANIMAL", "COW", 2],
                ["BUY_ANIMAL", "SHEEP", 2],
                ["BUY_SEED", "MELON", 12],
                ["BUY_SEED", "WHEAT", 7],
                ["BUY_PRODUCT", "WHEAT", 4],
                ["HIRE"],
                ["HIRE"],
                ["HIRE"],
                ["HIRE"]
            ]
        elif hour == 0:
            # Morning Liquidations
            fert_held = int(shed.get("FERTILIZER", 0) or 0)
            if fert_held > 0:
                market_orders.append(["SELL", "FERTILIZER", fert_held])

            milk_held = int(shed.get("MILK", 0) or 0)
            if milk_held > 0:
                market_orders.append(["SELL", "MILK", milk_held])
            wool_held = int(shed.get("WOOL", 0) or 0)
            if wool_held > 0:
                market_orders.append(["SELL", "WOOL", wool_held])

            melon_held = int(shed.get("MELON", 0) or 0)
            if melon_held > 0:
                market_orders.append(["SELL", "MELON", melon_held])

            straw_held = int(shed.get("STRAWBERRY", 0) or 0)
            if straw_held > 0:
                market_orders.append(["SELL", "STRAWBERRY", straw_held])

            # Feed safety: maintain 4 wheat in shed
            wheat_held = int(shed.get("WHEAT", 0) or 0)
            if wheat_held < 4 and money >= 100:
                market_orders.append(["BUY_PRODUCT", "WHEAT", min(4, int(money // 30))])

            # Hire 2 hands every morning (cost is $1 + $1 = $2!)
            hires_today = int(farm.get("hires_today", 0) or 0)
            target_hands = 2 if day < 11 else 4
            can_hire = min(10 - len(market_orders), max(0, target_hands - hires_today))
            for _ in range(can_hire):
                market_orders.append(["HIRE"])

        # =====================================================================
        # 2. FARMER LAYER (Pastures & Livestock Logistics)
        # =====================================================================
        farmer_act = ["PASS"]
        fx, fy = farmer_pos
        f_inv = inventories[0] if len(inventories) > 0 else {}
        f_tile = tiles[fy][fx] if 0 <= fy < BOARD_SIZE and 0 <= fx < BOARD_SIZE else None
        f_load = sum(f_inv.values())

        # Inspect pastures
        unbuilt_p = [p for p in PASTURE_NW if tiles[p[1]][p[0]] is None]
        empty_p = [p for p in PASTURE_NW if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("kind") == "PASTURE" and not tiles[p[1]][p[0]].get("animal")]
        hungry_p = [p for p in PASTURE_NW if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("animal") and not tiles[p[1]][p[0]].get("fed_today")]
        fert_p = [p for p in PASTURE_NW if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("fertilizer_available")]
        yield_p = [p for p in PASTURE_NW if isinstance(tiles[p[1]][p[0]], dict) and int(tiles[p[1]][p[0]].get("yield_units", 0) or 0) > 0]

        # Farmer action on current tile
        if f_tile is None and farmer_pos in PASTURE_NW:
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
        elif farmer_pos in SHED_TILES:
            # Shed operations: drop commodities only
            sellable_drops = any(k in ("FERTILIZER", "MILK", "WOOL", "MELON", "STRAWBERRY", "TOMATO", "CARROT", "EGG") for k, v in f_inv.items() if v > 0)
            excess_wheat = (len(hungry_p) == 0 and f_inv.get("WHEAT", 0) > 0)
            if sellable_drops or excess_wheat:
                farmer_act = ["DROP"]
            elif empty_p and f_load == 0:
                # Deliver animals first
                if shed.get("COW", 0) > 0:
                    farmer_act = ["PICKUP", "COW", 1]
                elif shed.get("SHEEP", 0) > 0:
                    farmer_act = ["PICKUP", "SHEEP", 1]
            elif not empty_p and hungry_p and f_inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0 and f_load == 0:
                # Deliver feed only when animals are placed
                farmer_act = ["PICKUP", "WHEAT", min(len(hungry_p), shed.get("WHEAT", 0))]

        # Farmer movement
        if farmer_act == ["PASS"]:
            target = None
            if unbuilt_p:
                target = unbuilt_p[0]
            elif f_inv.get("COW", 0) > 0 or f_inv.get("SHEEP", 0) > 0:
                target = empty_p[0] if empty_p else (4, 4)
            elif empty_p and (shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0) and f_load == 0:
                target = (4, 4)
            elif hungry_p:
                if f_inv.get("WHEAT", 0) > 0:
                    target = hungry_p[0]
                elif shed.get("WHEAT", 0) > 0:
                    target = (4, 4)
            elif fert_p:
                target = fert_p[0]
            elif yield_p:
                target = yield_p[0]
            elif f_load > 0:
                target = (4, 4)

            if target and target != farmer_pos:
                farmer_act = [bfs_step(farmer_pos, target, tiles)]

        # =====================================================================
        # 3. FIELD WORKERS LAYER (Dedicated Snake Paths)
        # =====================================================================
        hands_act = [["PASS"] for _ in hands_pos]

        # Dynamic path assignment: 4-way row split when 4 hands present, else 2-way split
        if len(hands_pos) >= 4:
            assigned_paths = [ROW0_PATH, ROW1_PATH, ROW2_PATH, ROW34_PATH]
        else:
            assigned_paths = [NORTH_PATH, SOUTH_PATH]

        for h_idx, h_pos in enumerate(hands_pos):
            if h_idx >= len(assigned_paths):
                # Extra hands assist with north/south or drop
                path = NORTH_PATH if h_idx % 2 == 0 else SOUTH_PATH
            else:
                path = assigned_paths[h_idx]

            hx, hy = h_pos
            w_idx = h_idx + 1
            h_inv = inventories[w_idx] if w_idx < len(inventories) else {}
            h_load = sum(h_inv.values())
            h_tile = tiles[hy][hx] if 0 <= hy < BOARD_SIZE and 0 <= hx < BOARD_SIZE else None

            h_act = ["PASS"]

            # Priority 1: If at shed and carrying items -> DROP
            if h_pos in SHED_TILES and h_load > 0:
                h_act = ["DROP"]
            # Priority 2: Tile action on current position
            elif isinstance(h_tile, dict) and h_tile.get("kind") == "PLANT":
                crop_name = h_tile.get("crop")
                age = day - int(h_tile.get("planted_day", 0) or 0)
                first_y = CROPS.get(crop_name, {}).get("first_yield", 2)
                if age >= first_y and int(h_tile.get("yield_units", 0) or 0) > 0:
                    h_act = ["HARVEST"]
                elif not h_tile.get("watered_today"):
                    h_act = ["WATER"]
            elif h_tile is None and h_pos in path:
                # Decide crop to plant: melons in rows 0, 1 and (0,2), (1,2)
                if (hy in (0, 1) or (hy == 2 and hx in (0, 1))) and seeds.get("MELON", 0) > 0:
                    h_act = ["PLANT", "MELON"]
                    seeds["MELON"] -= 1
                elif seeds.get("WHEAT", 0) > 0:
                    h_act = ["PLANT", "WHEAT"]
                    seeds["WHEAT"] -= 1

            # Priority 3: Movement along path to find uncompleted work
            if h_act == ["PASS"]:
                if h_load >= 3:
                    h_act = [bfs_step(h_pos, (4, 4), tiles)]
                else:
                    # Find first tile in path that needs work (unplanted, unwatered, or ripe)
                    next_target = None
                    for tp in path:
                        tx, ty = tp
                        tt = tiles[ty][tx]
                        if tt is None:
                            # Needs planting if seeds available
                            if (ty in (0, 1) or (ty == 2 and tx in (0, 1))) and seeds.get("MELON", 0) > 0:
                                next_target = tp
                                break
                            elif seeds.get("WHEAT", 0) > 0:
                                next_target = tp
                                break
                        elif isinstance(tt, dict) and tt.get("kind") == "PLANT":
                            c_name = tt.get("crop")
                            c_age = day - int(tt.get("planted_day", 0) or 0)
                            c_fy = CROPS.get(c_name, {}).get("first_yield", 2)
                            if c_age >= c_fy and int(tt.get("yield_units", 0) or 0) > 0:
                                next_target = tp
                                break
                            elif not tt.get("watered_today"):
                                next_target = tp
                                break

                    if next_target and next_target != h_pos:
                        h_act = [bfs_step(h_pos, next_target, tiles)]
                    elif h_load > 0 and h_pos not in SHED_TILES:
                        h_act = [bfs_step(h_pos, (4, 4), tiles)]

            hands_act[h_idx] = h_act

        return {
            "farmer": farmer_act,
            "hands": hands_act,
            "market": market_orders[:10]
        }

if __name__ == "__main__":
    agent = ZonedSnakeAgent()
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        obs0 = env.state[0].observation
        act0 = agent(obs0)
        act1 = v2.agent(env.state[1].observation)
        env.step([act0, act1])
        if s in (23, 47, 71, 119, 239, 263, 359, 479, 599, 718):
            f0 = env.state[0].observation["farms"][0]
            f1 = env.state[1].observation["farms"][1]
            p0 = env.state[0].observation["private"]
            # Count melons and unwatered
            melons = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
            unw = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today"))
            cows = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
            sheep = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
            print(f"Step {s:3d} (D{s//24:2d} H{s%24:2d}) | CL: Cash=${f0['money']:8.1f} Melons={melons:2d} Unw={unw:2d} Cows={cows} Sheep={sheep} Shed={p0['shed'].get('MELON', 0)}M {p0['shed'].get('FERTILIZER', 0)}F | V2 Cash=${f1['money']:8.1f}")
            
    print(f"\nFinal Reward: CL=${env.steps[-1][0]['reward']:,.1f} | V2=${env.steps[-1][1]['reward']:,.1f}")
