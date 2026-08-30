"""
ABLATION C — Batch 8 ONLY
Control + ONLY: sell_batch_size = 8. No other changes.
"""
import math

CROPS = {
    "WHEAT": {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 4},
    "CARROT": {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False, "base_yield": 3},
    "TOMATO": {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True, "base_yield": 4},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True, "base_yield": 4},
    "MELON": {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 6},
}
LAND_PRICES = [1000, 2000, 4000]

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
    sx, sy = start; tx, ty = target; moves = []
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

class AblationC_Batch8Only:
    SELL_BATCH = 8  # THE ONLY CHANGE vs control
    def __init__(self):
        self.target_cows = 8; self.target_sheep = 4; self.target_melons = 15; self.care_animals = True

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0); day = obs.get("day", 0); hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)
            farms = obs.get("farms", []); farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0)); farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0))
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))
            tiles = farm.get("tiles", [[None]*10 for _ in range(10)])
            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {})); seeds = dict(private.get("seeds", {}))
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]
            market = obs.get("market", {}) or {}; market_prices = dict(market.get("prices", {}))
            orders = []; chores = []; empty_tiles = []
            cow_count = 0; sheep_count = 0; pasture_count = 0
            empty_pastures = []; melon_plants = 0; unfed_animal_tiles = []

            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]; pos = (x, y)
                    if t is None: empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED": chores.append({"type": "DIG", "pos": pos, "weight": 95})
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a = t.get("animal")
                                if a == "COW": cow_count += 1
                                elif a == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False): chores.append({"type": "FEED", "pos": pos, "weight": 92}); unfed_animal_tiles.append(pos)
                                if self.care_animals and not t.get("cared_today", False): chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False): chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0: chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else: empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop == "MELON": melon_plants += 1
                            age = day - t.get("planted_day", 0); cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False): chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            if crop == "MELON":
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1): chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1): chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1): chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0: chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_t = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_t = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            total_animals = cow_count + sheep_count + cows_t + sheep_t

            total_c = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1: th = min(3, max(2, (total_c + 6) // 8))
            elif len(unlocked_quads) == 2: th = min(5, max(3, (total_c + 8) // 9))
            else: th = min(6, max(4, (total_c + 10) // 10))
            if hour == 0 and th > hires_today:
                for _ in range(th - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10: orders.append(["HIRE"]); money -= cost

            n_u = len(unlocked_quads) - 1
            if n_u < 2:
                cost = LAND_PRICES[n_u]
                if n_u == 0 and money >= cost + 250: orders.append(["BUY_LAND"]); money -= cost
                elif n_u == 1 and money >= cost + 500 and day <= 14: orders.append(["BUY_LAND"]); money -= cost

            spendable = max(0.0, money - 25.0)
            nc = max(0, self.target_cows - cow_count - cows_t); ns = max(0, self.target_sheep - sheep_count - sheep_t)
            co = 0; so = 0
            if day <= 12:
                if nc > 0 and spendable >= 695 and len(orders) < 10: orders.append(["BUY_ANIMAL", "COW", 1]); spendable -= 600; money -= 600; co += 1
                if ns > 0 and spendable >= 595 and len(orders) < 10: orders.append(["BUY_ANIMAL", "SHEEP", 1]); spendable -= 500; money -= 500; so += 1
            total_animals += co + so

            frt = total_animals * (4 if day < 26 else 0); wis = shed.get("WHEAT", 0)
            if wis < frt and spendable >= 25 and len(orders) < 10:
                wp = market_prices.get("WHEAT", 25); deficit = frt - wis
                tb = min(deficit, int(spendable // max(1, wp)), 15)
                if tb > 0: orders.append(["BUY_PRODUCT", "WHEAT", tb]); spendable -= tb * wp; money -= tb * wp

            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.target_melons and spendable >= 80 and len(orders) < 10:
                needed = self.target_melons - (melon_plants + seeds.get("MELON", 0))
                cb = min(needed, int(spendable // 80), 8)
                if cb > 0: orders.append(["BUY_SEED", "MELON", cb]); spendable -= cb * 80; money -= cb * 80
            if day >= 3 and day <= 26 and seeds.get("CARROT", 0) < 8 and spendable >= 40 and len(orders) < 10:
                cb = min(8 - seeds.get("CARROT", 0), int(spendable // 20), 6)
                if cb > 0: orders.append(["BUY_SEED", "CARROT", cb]); spendable -= cb * 20; money -= cb * 20

            # === ONLY CHANGE: batch size = 8 ===
            if step % 4 == 0 or step >= 680:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.SELL_BATCH if step < 680 else 30)
                        orders.append(["SELL", prod, batch])

            # Worker dispatch (identical to control)
            uptb = cows_t + sheep_t + co + so
            ptb = max(0, min(self.target_cows + self.target_sheep - pasture_count, uptb - len(empty_pastures)))
            wpos = [farmer_pos] + hands; unassigned = list(range(len(wpos)))
            actions = [["PASS"] for _ in range(len(wpos))]; assigned_pos = set()
            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles: chores.append({"type": "PLANT", "pos": pos, "weight": 70})
            av = dict(seeds)
            for w in list(unassigned):
                pos = wpos[w]; x, y = pos; t = tiles[y][x]; inv = inventories[w] if w < len(inventories) else {}
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED": actions[w] = ["DIG"]; unassigned.remove(w); assigned_pos.add(pos); continue
                    elif "animal" in t and t.get("animal"):
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]; inv["WHEAT"] -= 1; unassigned.remove(w); assigned_pos.add(pos)
                            if pos in unfed_animal_tiles: unfed_animal_tiles.remove(pos); continue
                        if t.get("yield_units", 0) > 0: actions[w] = ["HARVEST"]; unassigned.remove(w); assigned_pos.add(pos); continue
                        if t.get("fertilizer_available", False): actions[w] = ["COLLECT_FERTILIZER"]; unassigned.remove(w); assigned_pos.add(pos); continue
                        if self.care_animals and not t.get("cared_today", False): actions[w] = ["CARE"]; unassigned.remove(w); assigned_pos.add(pos); continue
                    elif kind == "PASTURE" and "animal" not in t:
                        if inv.get("COW", 0) > 0: actions[w] = ["PLACE", "COW"]; inv["COW"] -= 1; unassigned.remove(w); assigned_pos.add(pos); continue
                        elif inv.get("SHEEP", 0) > 0: actions[w] = ["PLACE", "SHEEP"]; inv["SHEEP"] -= 1; unassigned.remove(w); assigned_pos.add(pos); continue
                    elif kind == "PLANT":
                        if any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores): actions[w] = ["HARVEST"]; unassigned.remove(w); assigned_pos.add(pos); continue
                        if not t.get("watered_today", False): actions[w] = ["WATER"]; unassigned.remove(w); assigned_pos.add(pos); continue
                elif t is None:
                    if ptb > 0: actions[w] = ["BUILD_PASTURE"]; ptb -= 1; pasture_count += 1; empty_pastures.append(pos); unassigned.remove(w); assigned_pos.add(pos); continue
                    elif day <= 26:
                        for sc in ["MELON", "CARROT", "WHEAT"]:
                            if av.get(sc, 0) > 0: actions[w] = ["PLANT", sc]; av[sc] -= 1; unassigned.remove(w); assigned_pos.add(pos); break
            ushed = get_unlocked_shed_tiles(tiles)
            for w in list(unassigned):
                wp = wpos[w]; inv = inventories[w] if w < len(inventories) else {}
                if wp in ushed:
                    if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures: actions[w] = ["PICKUP", "COW", 1]; shed["COW"] -= 1; unassigned.remove(w); continue
                    elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures: actions[w] = ["PICKUP", "SHEEP", 1]; shed["SHEEP"] -= 1; unassigned.remove(w); continue
                    elif unfed_animal_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                        tq = min(4, shed["WHEAT"]); actions[w] = ["PICKUP", "WHEAT", tq]; shed["WHEAT"] -= tq; unassigned.remove(w); continue
            rc = [c for c in chores if c["pos"] not in assigned_pos]; cu = set()
            for w in list(unassigned):
                wp = wpos[w]; inv = inventories[w] if w < len(inventories) else {}
                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    if empty_pastures: t2 = min(empty_pastures, key=lambda p: manhattan(wp, p)); actions[w] = [get_next_step(wp, t2, tiles)]; unassigned.remove(w); continue
                if inv.get("WHEAT", 0) > 0 and unfed_animal_tiles:
                    au = [p for p in unfed_animal_tiles if p not in cu]
                    t2 = min(au or unfed_animal_tiles, key=lambda p: manhattan(wp, p)); cu.add(t2); actions[w] = [get_next_step(wp, t2, tiles)]; unassigned.remove(w); continue
                if inv.get("WHEAT", 0) == 0 and unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                    if len(cu) < len(unfed_animal_tiles) and ushed: actions[w] = [get_next_step(wp, ushed[0], tiles)]; unassigned.remove(w); continue
            for w in unassigned:
                wp = wpos[w]
                if rc:
                    best = max(rc, key=lambda c: c["weight"] - manhattan(wp, c["pos"]) * 2.0)
                    actions[w] = [get_next_step(wp, best["pos"], tiles)]; assigned_pos.add(best["pos"]); rc.remove(best); continue
                if wp not in ushed and ushed: actions[w] = [get_next_step(wp, ushed[0], tiles)]
                else: actions[w] = ["PASS"]
            return {"farmer": actions[0], "hands": actions[1:] if len(actions) > 1 else [], "market": orders[:10]}
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

_instance = AblationC_Batch8Only()
def agent(obs, configuration=None):
    return _instance(obs, configuration)
