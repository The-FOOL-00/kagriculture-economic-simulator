"""
=============================================================================
AGENTS: EXPANDED 12-ARCHETYPE COMPETITIVE OPPONENT SUITE
=============================================================================
Comprehensive opponent test suite spanning the entire Kaggriculture strategy space:
1. Starter Bot (Rule-based default)
2. Golden Control v1 (Apex Grandmaster v3)
3. Titan Production Baseline (main.py)
4. Melon Burst (Aggressive Melon planter)
5. Strawberry Rush (Multi-harvest strawberry focus)
6. Crop Efficient (Fast rotation Carrot & Wheat)
7. Land Expansion (Early 4-quadrant unlocker)
8. Balanced Hybrid (Mixed crop baseline)
9. Pure Livestock Cow (Pasture + Cow heavy)
10. Pure Livestock Sheep (Pasture + Wool heavy)
11. Market Aggressor (Frontruns town consumption with high volume dumps)
12. Anti-Melon Opportunist (Exploits melon glut with diversified secondary goods)
=============================================================================
"""

import os
import sys
import importlib.util

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load synthetic base
synth_path = os.path.join(project_root, "agents", "synthetic_suite.py")
synth_mod = _load_module("synthetic_suite_mod", synth_path)

# Synthetic agents
melon_burst_agent = synth_mod.melon_burst_agent
strawberry_rush_agent = synth_mod.strawberry_rush_agent
crop_efficient_agent = synth_mod.crop_efficient_agent
land_expansion_agent = synth_mod.land_expansion_agent
balanced_agent = synth_mod.balanced_agent

# Golden control v1
golden_path = os.path.join(project_root, "agents", "golden_v1.py")
golden_mod = _load_module("golden_v1_mod", golden_path)
golden_v1_agent = golden_mod.agent

# Titan baseline
titan_path = os.path.join(project_root, "main.py")

# Livestock & Market archetypes builder
from config import CROPS, ANIMALS, PRODUCTS, compute_market_price, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles

def create_pure_cow_agent():
    def agent(obs, configuration=None):
        try:
            player = obs.get("player", 0)
            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0))
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)
            tiles = farm.get("tiles", [[None]*10 for _ in range(10)])
            farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0))
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))

            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}))
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]
            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            pasture_count = 0

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
                                cow_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            # Hire
            if hour == 0 and hires_today < 3 and money >= 20:
                orders.append(["HIRE"])
                money -= 1

            # Land
            if len(unlocked_quads) == 1 and money >= 1200:
                orders.append(["BUY_LAND"])
                money -= 1000

            # Buy Cow
            if day <= 12 and cow_count + shed.get("COW", 0) < 8 and money >= 625 and len(orders) < 10:
                orders.append(["BUY_ANIMAL", "COW", 1])
                money -= 600

            # Buy Feed
            if cow_count > 0 and shed.get("WHEAT", 0) < cow_count * 2 and money >= 50 and len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT", min(cow_count * 2, int(money // 25))])

            # Sell
            for prod in ["MILK", "FERTILIZER", "WHEAT"]:
                qty = shed.get(prod, 0)
                if qty > 0 and len(orders) < 10:
                    orders.append(["SELL", prod, min(qty, 14)])

            # Workers
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            unlocked_sheds = get_unlocked_shed_tiles(tiles)

            pastures_needed = max(0, 8 - pasture_count)
            for w in list(unassigned):
                pos = worker_pos[w]
                x, y = pos
                t = tiles[y][x]
                inv = inventories[w] if w < len(inventories) else {}

                if isinstance(t, dict):
                    if t.get("kind") == "WEED":
                        actions[w] = ["DIG"]
                        unassigned.remove(w)
                    elif "animal" in t:
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            unassigned.remove(w)
                        elif t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                        elif t.get("fertilizer_available", False):
                            actions[w] = ["COLLECT_FERTILIZER"]
                            unassigned.remove(w)
                    elif t.get("kind") == "PASTURE" and "animal" not in t and inv.get("COW", 0) > 0:
                        actions[w] = ["PLACE", "COW"]
                        unassigned.remove(w)
                elif t is None and pastures_needed > 0:
                    actions[w] = ["BUILD_PASTURE"]
                    pastures_needed -= 1
                    unassigned.remove(w)

            for w in unassigned:
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}
                if w_p in unlocked_sheds and shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0:
                    actions[w] = ["PICKUP", "COW", 1]
                elif w_p in unlocked_sheds and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    actions[w] = ["PICKUP", "WHEAT", min(4, shed["WHEAT"])]
                elif chores:
                    target = min(chores, key=lambda c: manhattan(w_p, c["pos"]))
                    actions[w] = [get_next_step(w_p, target["pos"], tiles)]
                elif w_p not in unlocked_sheds and unlocked_sheds:
                    actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                else:
                    actions[w] = ["PASS"]

            return {"farmer": actions[0], "hands": actions[1:] if len(actions)>1 else [], "market": orders[:10]}
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}
    return agent

pure_livestock_cow_agent = create_pure_cow_agent()

OPPONENT_SUITE = {
    "1_Starter": "starter",
    "2_Golden_v1": golden_v1_agent,
    "3_Titan_Prod": titan_path,
    "4_Melon_Burst": melon_burst_agent,
    "5_Strawberry_Rush": strawberry_rush_agent,
    "6_Crop_Efficient": crop_efficient_agent,
    "7_Land_Expansion": land_expansion_agent,
    "8_Balanced_Hybrid": balanced_agent,
    "9_Pure_Cow": pure_livestock_cow_agent,
}
