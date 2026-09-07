"""
Candidate CL-Aethel v5 – High-Performance Closed-Loop Architecture.
===================================================================
100% closed-loop, observation-driven. Zero replay tapes.

Key Architectural Principles:
  1. Clustered 14-pasture layout tightly packed around shed-access tiles (4,4), (5,4), (4,5).
  2. Strict pasture build-on-demand: ONLY build a pasture when an animal is owned.
  3. Day-0 Economic Flywheel:
     - Buy 3 cows, 1 sheep, 7 melons, 10 wheat seeds, 17 wheat feed, hire 5 workers.
     - Plant 10 wheat (matures Day 2 -> 40-60 feed, achieves feed self-sufficiency).
     - Plant 7 melons (matures Day 10 -> ~$10,500 cash surge).
  4. Compound Reinvestment:
     - Day 7: Buy Land NE ($1,000). Expand herd + strawberry orchards.
     - Day 10: Sell 42 melons ($10,500). Buy Land SW ($2,000). Herd scales to 14.
     - Flood NE and SW with 40+ continuous-yielding strawberries.
  5. Wave 2 Melons (Days 11-15) + Late-Game Wheat Rush (Day 26).
  6. Strict P0 chore discipline:
     - Plants: WATER first (prevents death, enables continuous yield).
     - Animals: FEED first (prevents escape, enables daily milk/wool/fertilizer).
  7. Terminal liquidation engine for steps 712-720.
"""

BOARD = 10
TPD   = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

# Ordered clustered pasture layout (14 slots total, matching 8 cows + 6 sheep)
PASTURE_SLOTS = [
    # NW quadrant (8 slots, clustered around shed access (4,4))
    (4, 4), (4, 3), (3, 4), (4, 2), (3, 3), (3, 2), (2, 4), (0, 2),
    # NE quadrant (5 slots, unlocked Day 7+, clustered around (5,4))
    (5, 4), (6, 4), (7, 4), (5, 3), (6, 3),
    # SW quadrant (1 slot, unlocked Day 10+, at (4,5))
    (4, 5),
]

# Day 0 designated crop layouts
MELON_DAY0 = frozenset([(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (2, 1), (3, 1)])
WHEAT_DAY0 = frozenset([(0, 1), (1, 1), (4, 1), (1, 2), (2, 2), (0, 3), (1, 3), (2, 3), (0, 4), (3, 2)])

CROPS_D = {
    "MELON":      {"seed": 80,  "fy": 10, "ongoing": False},
    "STRAWBERRY": {"seed": 100, "fy": 10, "ongoing": True},
    "WHEAT":      {"seed": 10,  "fy": 2,  "ongoing": False},
}
SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")

MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _fib(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a + b
    return a


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _walkable(x, y, tiles):
    if not (0 <= x < BOARD and 0 <= y < BOARD): return False
    return tiles[y][x] != "LOCKED"


def _bfs(start, goal, tiles):
    if start == goal: return "PASS"
    sx, sy = start; gx, gy = goal
    if _dist(start, goal) == 1:
        for m, (dx, dy) in MOVES.items():
            if sx + dx == gx and sy + dy == gy and _walkable(gx, gy, tiles): return m
    q = [start]; vis = {start: None}; head = 0
    while head < len(q):
        cx, cy = q[head]; head += 1
        if (cx, cy) == goal: break
        for m, (dx, dy) in MOVES.items():
            nx, ny = cx + dx, cy + dy
            if _walkable(nx, ny, tiles) and (nx, ny) not in vis:
                vis[(nx, ny)] = ((cx, cy), m); q.append((nx, ny))
    if goal not in vis or vis[goal] is None:
        best, bd = "PASS", 999
        for m, (dx, dy) in MOVES.items():
            nx, ny = sx + dx, sy + dy
            if _walkable(nx, ny, tiles):
                d = _dist((nx, ny), goal)
                if d < bd: bd, best = d, m
        return best
    cur = goal
    while vis[cur] is not None:
        prev, mv = vis[cur]
        if prev == start: return mv
        cur = prev
    return "PASS"


def _ns(pos, tiles):
    cands = [(x, y) for x, y in SHED_ACCESS if tiles[y][x] != "LOCKED"]
    return min(cands, key=lambda p: _dist(pos, p)) if cands else (4, 4)


def _quad(x, y):
    if y < 5: return "NW" if x < 5 else "NE"
    return "SW" if x < 5 else "SE"


def _go(pos, tgt, tiles):
    if pos == tgt: return "PASS"
    return _bfs(pos, tgt, tiles)


class CLAethelV5:
    """High-Performance Closed-Loop Agent."""

    def __init__(self):
        self._step = -1

    def __call__(self, obs, config=None):
        day  = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        raw  = obs.get("step")
        step = int(raw) if raw is not None else day * TPD + hour

        if step == 0 or step <= self._step: self._step = -1
        self._step = step

        p     = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm  = farms[p] if p < len(farms) else {}
        priv  = obs.get("private") or {}
        shed  = dict(priv.get("shed") or {})
        seeds = dict(priv.get("seeds") or {})
        invs  = list(priv.get("inventories") or [])

        tiles      = farm.get("tiles") or []
        farmer_pos = tuple(farm.get("farmer") or [4, 4])
        hands_pos  = [tuple(h) for h in (farm.get("hands") or [])]
        money      = float(farm.get("money") or 0)
        quads      = farm.get("unlocked_quadrants") or ["NW"]
        hired      = int(farm.get("hires_today") or 0)

        if step >= 712:
            return self._terminal(tiles, [farmer_pos] + hands_pos, invs, shed, obs)

        all_workers = [farmer_pos] + hands_pos
        all_invs    = list(invs) + [{} for _ in range(len(all_workers) - len(invs))]

        # ── Market ──────────────────────────────────────────────────────────
        orders = self._market(step, day, hour, money, quads, tiles, shed, seeds, hired, all_invs)

        # ── Field scan ──────────────────────────────────────────────────────
        (unbuilt_p, empty_p, hungry, ripe_a, fert,
         unwatered, ripe_plants, plant_m, plant_s, plant_w, weeds) = self._scan(
            tiles, quads, seeds, shed, all_invs, day
        )

        # ── Worker roles ─────────────────────────────────────────────────
        assigned_w   = set()  # claimed unwatered tiles
        assigned_f   = set()  # claimed hungry pastures
        assigned_h   = set()  # claimed harvest tiles
        assigned_pl  = set()  # claimed planting sites
        assigned_b   = set()  # claimed build sites

        animals_field = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal"))
        animals_shed  = int(shed.get("COW") or 0) + int(shed.get("SHEEP") or 0)
        animals_inv   = sum(int(inv.get("COW", 0) or 0) + int(inv.get("SHEEP", 0) or 0) for inv in all_invs)
        total_animals = animals_field + animals_shed + animals_inv

        # Determine number of livestock workers based on total animals owned:
        if total_animals >= 10:
            n_livestock_workers = 4   # farmer + 3 hands
        elif total_animals >= 7:
            n_livestock_workers = 3   # farmer + 2 hands
        elif total_animals >= 3:
            n_livestock_workers = 2   # farmer + 1 hand
        else:
            n_livestock_workers = 1   # farmer only

        acts = []
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if i == 0:
                is_livestock = True  # farmer is lead livestock specialist
            elif i < n_livestock_workers:
                is_livestock = True  # assigned livestock helpers
            else:
                is_livestock = False # dedicated crop workers

            if is_livestock:
                a = self._livestock_worker(
                    pos, inv, tiles, shed, quads, day, hour,
                    unbuilt_p, empty_p, hungry, ripe_a, fert, weeds,
                    assigned_f, assigned_h, assigned_b
                )
            else:
                a = self._crop_worker(
                    pos, inv, tiles, seeds, shed, quads, day, hour,
                    unwatered, ripe_plants, plant_m, plant_s, plant_w, weeds,
                    assigned_w, assigned_h, assigned_pl
                )
            acts.append(a)

        return {"farmer": acts[0], "hands": acts[1:], "market": orders[:10]}

    # ── Market controller ─────────────────────────────────────────────────
    def _market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs):
        orders = []
        BASE_PRICE = {
            "MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200,
            "EGG": 50, "FERTILIZER": 100, "CARROT": 35, "TOMATO": 60, "WHEAT": 25
        }

        if step == 0:
            # Proven Day-0 Economic Opening:
            # 3 cows ($1200) + 1 sheep ($500) + 7 melon seeds ($560) + 10 wheat seeds ($100) + 17 feed ($473) + 2 hires ($2) = $2835
            return [
                ["BUY_ANIMAL", "COW", 3],
                ["BUY_ANIMAL", "SHEEP", 1],
                ["BUY_SEED", "MELON", 7],
                ["BUY_SEED", "WHEAT", 10],
                ["BUY_PRODUCT", "WHEAT", 17],
                ["HIRE"], ["HIRE"],
            ]

        # Day 0 staggered hires
        if day == 0 and hour in (1, 2, 5) and hired < 5:
            orders.append(["HIRE"])

        # Morning batch at H0
        if hour == 0:
            cows_field  = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
            sheep_field = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
            cows_tot    = cows_field + int(shed.get("COW") or 0)
            sheep_tot   = sheep_field + int(shed.get("SHEEP") or 0)
            n_anim      = cows_tot + sheep_tot

            # 1. SELLS FIRST: Liquidation of produce to fund subsequent buys
            shed_liquid = 0
            for item in ["MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "FERTILIZER", "CARROT", "TOMATO"]:
                qty = int(shed.get(item) or 0)
                if qty > 0 and len(orders) < 8:
                    orders.append(["SELL", item, qty])
                    shed_liquid += qty * BASE_PRICE.get(item, 50)

            # Wheat sales: sell surplus above 3 days feed buffer
            wheat_shed = int(shed.get("WHEAT") or 0)
            wheat_buffer = max(10, n_anim * 3)
            if wheat_shed > wheat_buffer and len(orders) < 8:
                surplus = wheat_shed - wheat_buffer
                orders.append(["SELL", "WHEAT", surplus])
                shed_liquid += surplus * 25

            effective_money = money + shed_liquid

            # 2. LAND UNLOCKS:
            if len(quads) == 1 and effective_money >= 1100 and day >= 7 and len(orders) < 9:
                orders.append(["BUY_LAND"])
                effective_money -= 1000
            elif len(quads) == 2 and effective_money >= 2200 and day >= 10 and len(orders) < 9:
                orders.append(["BUY_LAND"])
                effective_money -= 2000

            # 3. ANIMAL SCALING:
            if "NE" in quads and day >= 7 and day <= 22 and len(orders) < 9:
                target_cows  = 5 if len(quads) == 2 else 8
                target_sheep = 3 if len(quads) == 2 else 6
                if cows_tot < target_cows and effective_money >= 600:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    effective_money -= 400
                elif sheep_tot < target_sheep and effective_money >= 700:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    effective_money -= 500

            # 4. STRAWBERRY SEEDS:
            if day >= 4 and day <= 22 and len(orders) < 9:
                straw_f = sum(1 for row in tiles for t in row
                              if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
                straw_s = int(seeds.get("STRAWBERRY") or 0)
                target_straw = 22 if len(quads) == 1 else (35 if len(quads) == 2 else 45)
                straw_need = max(0, target_straw - straw_f - straw_s)
                if straw_need > 0 and effective_money >= 300:
                    can = min(straw_need, int((effective_money - 200) // 100))
                    if can > 0:
                        orders.append(["BUY_SEED", "STRAWBERRY", can])
                        effective_money -= can * 100

            # 5. WAVE 2 MELONS (Days 11-15):
            if day in (11, 12, 13, 14, 15) and len(orders) < 9:
                melon_f = sum(1 for row in tiles for t in row
                              if isinstance(t, dict) and t.get("crop") == "MELON")
                melon_s = int(seeds.get("MELON") or 0)
                melon_need = max(0, 12 - melon_f - melon_s)
                if melon_need > 0 and effective_money >= 400:
                    can = min(melon_need, int((effective_money - 200) // 80))
                    if can > 0:
                        orders.append(["BUY_SEED", "MELON", can])
                        effective_money -= can * 80

            # 6. LATE-GAME WHEAT RUSH (Day 26):
            if day == 26 and len(orders) < 9:
                wheat_s = int(seeds.get("WHEAT") or 0)
                if wheat_s < 25 and effective_money >= 300:
                    orders.append(["BUY_SEED", "WHEAT", 25])
                    effective_money -= 250

            # 7. FEED STARVATION PREVENTION:
            have_wheat = int(shed.get("WHEAT") or 0)
            wheat_need = max(0, n_anim * 2 - have_wheat)
            if wheat_need > 0 and effective_money >= 100 and len(orders) < 9:
                can = min(wheat_need, int(effective_money // 25))
                if can > 0:
                    orders.append(["BUY_PRODUCT", "WHEAT", can])
                    effective_money -= can * 25

        # ── Dynamic Hiring Schedule ─────────────────────────────────────────
        if day < 4:    target_h = 5
        elif day < 7:  target_h = 6
        elif day < 10: target_h = 8
        elif day < 16: target_h = 10
        else:          target_h = 12

        cur_h = hired
        budget = money
        while cur_h < target_h and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]

    # ── Field Scan ────────────────────────────────────────────────────────
    def _scan(self, tiles, quads, seeds, shed, invs, day):
        unbuilt_p = []; empty_p = []; hungry = []; ripe_a = []; fert = []
        unwatered = []; ripe_plants = []; plant_m = []; plant_s = []; plant_w = []; weeds = []

        # Count animals owned to strictly determine valid pasture slots
        animals_field = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal"))
        animals_shed  = int(shed.get("COW") or 0) + int(shed.get("SHEEP") or 0)
        animals_inv   = sum(int(inv.get("COW", 0) or 0) + int(inv.get("SHEEP", 0) or 0) for inv in invs)
        total_animals = animals_field + animals_shed + animals_inv

        target_pastures = min(len(PASTURE_SLOTS), total_animals)
        valid_pasture_slots = set(PASTURE_SLOTS[:target_pastures])

        for y in range(BOARD):
            for x in range(BOARD):
                pos = (x, y)
                t = tiles[y][x] if tiles else None
                q = _quad(x, y)
                if q not in quads: continue
                if t == "LOCKED": continue

                if t is None:
                    if pos in valid_pasture_slots:
                        unbuilt_p.append(pos)
                    else:
                        # Open crop tile
                        if day < 3:
                            if pos in MELON_DAY0 and int(seeds.get("MELON") or 0) > 0:
                                plant_m.append(pos)
                            elif pos in WHEAT_DAY0 and int(seeds.get("WHEAT") or 0) > 0:
                                plant_w.append(pos)
                            elif int(seeds.get("STRAWBERRY") or 0) > 0:
                                plant_s.append(pos)
                            elif int(seeds.get("MELON") or 0) > 0:
                                plant_m.append(pos)
                            elif int(seeds.get("WHEAT") or 0) > 0:
                                plant_w.append(pos)
                        else:
                            if int(seeds.get("STRAWBERRY") or 0) > 0:
                                plant_s.append(pos)
                            elif int(seeds.get("MELON") or 0) > 0 and day <= 16:
                                plant_m.append(pos)
                            elif int(seeds.get("WHEAT") or 0) > 0 and (day >= 26 or int(shed.get("WHEAT") or 0) < total_animals * 2):
                                plant_w.append(pos)
                    continue

                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PASTURE":
                        if t.get("animal"):
                            if not t.get("fed_today"): hungry.append(pos)
                            if int(t.get("yield_units") or 0) > 0: ripe_a.append(pos)
                            if t.get("fertilizer_available"): fert.append(pos)
                        else:
                            empty_p.append(pos)
                    elif k == "PLANT":
                        age = day - int(t.get("planted_day") or 0)
                        fy  = CROPS_D.get(t.get("crop"), {}).get("fy", 2)
                        if not t.get("watered_today"): unwatered.append(pos)
                        if int(t.get("yield_units") or 0) > 0 and age >= fy: ripe_plants.append(pos)
                    elif k == "WEED":
                        weeds.append(pos)

        return (unbuilt_p, empty_p, hungry, ripe_a, fert,
                unwatered, ripe_plants, plant_m, plant_s, plant_w, weeds)

    # ── Livestock worker ──────────────────────────────────────────────────
    def _livestock_worker(self, pos, inv, tiles, shed, quads, day, hour,
                          unbuilt_p, empty_p, hungry, ripe_a, fert, weeds,
                          assigned_f, assigned_h, assigned_b):
        x, y = pos
        tile = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
        ns = _ns(pos, tiles)
        cow_inv   = int(inv.get("COW") or 0)
        sheep_inv = int(inv.get("SHEEP") or 0)
        wheat_inv = int(inv.get("WHEAT") or 0)
        non_wheat_load = sum(max(0, int(v or 0)) for k, v in inv.items() if k != "WHEAT")

        # ── 1. Actions on current tile ──────────────────────────────
        if pos in SHED_ACCESS and tiles[y][x] != "LOCKED":
            # Drop sellables first
            if any(k in SELLABLE and k != "WHEAT" and v > 0 for k, v in inv.items()):
                return ["DROP"]
            # Pickup animals if unstocked pastures exist (empty or unbuilt)
            unstocked = len([e for e in empty_p if e not in assigned_b]) + len([u for u in unbuilt_p if u not in assigned_b])
            if (cow_inv + sheep_inv) == 0 and unstocked > 0 and wheat_inv == 0:
                if int(shed.get("COW") or 0) > 0:
                    return ["PICKUP", "COW", min(2, int(shed.get("COW")), unstocked)]
                elif int(shed.get("SHEEP") or 0) > 0:
                    return ["PICKUP", "SHEEP", min(2, int(shed.get("SHEEP")), unstocked)]

            # Pickup wheat if hungry animals
            n_hungry_unclaimed = len([h for h in hungry if h not in assigned_f])
            if n_hungry_unclaimed > 0 and int(shed.get("WHEAT") or 0) > 0 and (cow_inv + sheep_inv) == 0 and wheat_inv == 0:
                return ["PICKUP", "WHEAT", min(4, n_hungry_unclaimed, int(shed.get("WHEAT")))]

        if isinstance(tile, dict):
            k = tile.get("kind")
            if k == "PASTURE":
                if tile.get("animal"):
                    # Feed hungry animal
                    if not tile.get("fed_today") and pos in hungry and pos not in assigned_f:
                        if wheat_inv > 0:
                            assigned_f.add(pos)
                            return ["FEED"]
                    # Harvest milk / wool
                    if int(tile.get("yield_units") or 0) > 0 and pos in ripe_a and pos not in assigned_h:
                        assigned_h.add(pos)
                        return ["HARVEST"]
                    # Collect fertilizer
                    if tile.get("fertilizer_available") and pos in fert:
                        return ["COLLECT_FERTILIZER"]
                else:
                    # Place animal into empty pasture
                    if cow_inv > 0 and pos in empty_p and pos not in assigned_b:
                        assigned_b.add(pos)
                        return ["PLACE", "COW"]
                    if sheep_inv > 0 and pos in empty_p and pos not in assigned_b:
                        assigned_b.add(pos)
                        return ["PLACE", "SHEEP"]
            elif k == "WEED":
                return ["DIG"]
        elif tile is None and pos in unbuilt_p and pos not in assigned_b:
            # Build pasture on valid slot
            assigned_b.add(pos)
            return ["BUILD_PASTURE"]

        # Drop overload / EOD
        if non_wheat_load > 0 and (hour >= 22 or non_wheat_load >= 5):
            return [_go(pos, ns, tiles)]
        if wheat_inv > 0 and hour >= 22 and not hungry:
            return [_go(pos, ns, tiles)]

        # ── 2. Routing ────────────────────────────────────────────────
        target = None

        # Priority 1: Place animals (if carrying)
        if target is None and (cow_inv + sheep_inv) > 0:
            cands = [e for e in empty_p if e not in assigned_b]
            if not cands:
                cands = [u for u in unbuilt_p if u not in assigned_b]
            if cands:
                t = min(cands, key=lambda p: _dist(pos, p))
                assigned_b.add(t)
                target = t

        # Priority 2: Feed hungry animals (if carrying wheat)
        if target is None and wheat_inv > 0:
            cands = [h for h in hungry if h not in assigned_f]
            if cands:
                t = min(cands, key=lambda p: _dist(pos, p))
                assigned_f.add(t)
                target = t

        # Priority 3: Fetch animals from shed if unstocked pastures exist
        unstocked = len([e for e in empty_p if e not in assigned_b]) + len([u for u in unbuilt_p if u not in assigned_b])
        if target is None and unstocked > 0 and (cow_inv + sheep_inv) == 0:
            if (int(shed.get("COW") or 0) + int(shed.get("SHEEP") or 0)) > 0:
                target = ns

        # Priority 4: Fetch wheat from shed (if hungry animals and wheat in shed)
        if target is None and hungry and wheat_inv == 0:
            cands = [h for h in hungry if h not in assigned_f]
            if cands and int(shed.get("WHEAT") or 0) > 0:
                target = ns

        # Priority 5: Build unbuilt pastures
        if target is None and unbuilt_p:
            cands = [u for u in unbuilt_p if u not in assigned_b]
            if cands:
                t = min(cands, key=lambda p: _dist(pos, p))
                assigned_b.add(t)
                target = t

        # Priority 6: Harvest ripe animals
        if target is None and ripe_a:
            cands = [r for r in ripe_a if r not in assigned_h]
            if cands:
                t = min(cands, key=lambda p: _dist(pos, p))
                assigned_h.add(t)
                target = t

        # Priority 7: Collect fertilizer
        if target is None and fert:
            target = min(fert, key=lambda p: _dist(pos, p))

        # Priority 8: Drop loaded goods
        if target is None and non_wheat_load > 0:
            target = ns

        if target and target != pos:
            return [_go(pos, target, tiles)]
        return ["PASS"]

    # ── Crop worker ───────────────────────────────────────────────────────
    def _crop_worker(self, pos, inv, tiles, seeds, shed, quads, day, hour,
                     unwatered, ripe_plants, plant_m, plant_s, plant_w, weeds,
                     assigned_w, assigned_h, assigned_pl):
        x, y = pos
        tile = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
        load = sum(max(0, int(v or 0)) for v in inv.values())
        ns = _ns(pos, tiles)

        # ── 1. Action on current tile ──────────────────────────────
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop")
            age = day - int(tile.get("planted_day") or 0)
            fy  = CROPS_D.get(crop, {}).get("fy", 2)
            units = int(tile.get("yield_units") or 0)

            # Water first (P0 priority — prevents plant death!)
            if not tile.get("watered_today") and pos in unwatered and pos not in assigned_w:
                assigned_w.add(pos)
                return ["WATER"]
            # Harvest ripe plant
            if units > 0 and age >= fy and pos in ripe_plants and pos not in assigned_h:
                assigned_h.add(pos)
                return ["HARVEST"]
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]
        elif tile is None and pos not in SHED_ACCESS:
            # Plant on open tile
            if pos in plant_s and pos not in assigned_pl:
                if int(seeds.get("STRAWBERRY") or 0) > 0:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    assigned_pl.add(pos)
                    return ["PLANT", "STRAWBERRY"]
            if pos in plant_m and pos not in assigned_pl:
                if int(seeds.get("MELON") or 0) > 0:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    assigned_pl.add(pos)
                    return ["PLANT", "MELON"]
            if pos in plant_w and pos not in assigned_pl:
                if int(seeds.get("WHEAT") or 0) > 0:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    assigned_pl.add(pos)
                    return ["PLANT", "WHEAT"]

        # Drop goods at shed
        if pos in SHED_ACCESS and load > 0:
            return ["DROP"]

        # EOD drop
        if load > 0 and (hour >= 22 or load >= 5):
            return [_go(pos, ns, tiles)]

        # ── 2. Routing ────────────────────────────────────────────────
        target = None

        # Priority 1: Water unwatered plants (P0 — prevents death!)
        cands = [u for u in unwatered if u not in assigned_w]
        if cands:
            t = min(cands, key=lambda p: _dist(pos, p))
            assigned_w.add(t)
            target = t

        # Priority 2: Plant strawberries
        if target is None and int(seeds.get("STRAWBERRY") or 0) > 0:
            ps = [p for p in plant_s if p not in assigned_pl]
            if ps:
                t = min(ps, key=lambda p: _dist(pos, p))
                assigned_pl.add(t)
                target = t

        # Priority 3: Plant melons
        if target is None and int(seeds.get("MELON") or 0) > 0:
            pm = [p for p in plant_m if p not in assigned_pl]
            if pm:
                t = min(pm, key=lambda p: _dist(pos, p))
                assigned_pl.add(t)
                target = t

        # Priority 4: Plant wheat
        if target is None and int(seeds.get("WHEAT") or 0) > 0:
            pw = [p for p in plant_w if p not in assigned_pl]
            if pw:
                t = min(pw, key=lambda p: _dist(pos, p))
                assigned_pl.add(t)
                target = t

        # Priority 5: Harvest ripe crops
        if target is None and ripe_plants:
            cands = [r for r in ripe_plants if r not in assigned_h]
            if cands:
                t = min(cands, key=lambda p: _dist(pos, p))
                assigned_h.add(t)
                target = t

        # Priority 6: Clear weeds
        if target is None and weeds:
            target = min(weeds, key=lambda p: _dist(pos, p))

        # Priority 7: Drop goods if carrying anything
        if target is None and load > 0:
            target = ns

        if target and target != pos:
            return [_go(pos, target, tiles)]
        return ["PASS"]

    # ── Terminal engine ───────────────────────────────────────────────────
    def _terminal(self, tiles, workers, invs, shed, obs):
        invs = list(invs) + [{} for _ in range(len(workers) - len(invs))]
        sheds = [(x, y) for x, y in SHED_ACCESS if tiles[y][x] != "LOCKED"]
        ripe = {
            (x, y) for y in range(BOARD) for x in range(BOARD)
            if isinstance(tiles[y][x], dict) and int(tiles[y][x].get("yield_units") or 0) > 0
        }
        acts, pending = [], {}
        for pos, inv in zip(workers, invs):
            inv = inv or {}
            load = sum(max(0, int(v or 0)) for v in inv.values())
            x, y = pos
            tile = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            ns = min(sheds, key=lambda s: _dist(pos, s)) if sheds else pos
            if load > 0 and pos in SHED_ACCESS:
                for k, v in inv.items():
                    if k in SELLABLE:
                        pending[k] = pending.get(k, 0) + max(0, int(v or 0))
                acts.append(["DROP"])
            elif isinstance(tile, dict) and int(tile.get("yield_units") or 0) > 0:
                ripe.discard(pos)
                acts.append(["HARVEST"])
            elif load > 0:
                acts.append([_go(pos, ns, tiles)])
            elif ripe:
                t = min(ripe, key=lambda r: (_dist(pos, r), r[1], r[0]))
                ripe.discard(t)
                acts.append([_go(pos, t, tiles)])
            elif isinstance(tile, dict) and tile.get("fertilizer_available"):
                acts.append(["COLLECT_FERTILIZER"])
            else:
                acts.append(["PASS"])

        merged = dict(shed)
        for k, v in pending.items():
            merged[k] = int(merged.get(k, 0) or 0) + v
        prices = (obs.get("market") or {}).get("prices") or {}
        sells = [
            (int(merged.get(i, 0) or 0) * float(prices.get(i, 1) or 1), i, int(merged.get(i, 0) or 0))
            for i in SELLABLE if int(merged.get(i, 0) or 0) > 0
        ]
        sells.sort(reverse=True)
        market = [["SELL", i, q] for _, i, q in sells[:10]]
        return {"farmer": acts[0], "hands": acts[1:], "market": market}


_inst = CLAethelV5()

def agent(obs, config=None):
    """Entrypoint for CL-Aethel v5."""
    return _inst(obs, config)
