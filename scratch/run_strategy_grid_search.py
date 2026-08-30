import os
import sys
import time
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import CROPS, ANIMALS, PRODUCTS, MARKET_PARAMS, compute_market_price, fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles

# Parametric Agent Class
class ParametricStrategy:
    def __init__(
        self,
        name="Parametric",
        target_cows=8,
        target_sheep=4,
        target_geese=0,
        target_melons=15,
        secondary_crop="CARROT",
        secondary_target=8,
        sell_batch_size=24,
        emergency_liquidity=True,
        care_animals=True,
        feed_buffer_days=4,
        day0_land=True,
        dynamic_elasticity=False
    ):
        self.name = name
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = target_geese
        self.target_melons = target_melons
        self.secondary_crop = secondary_crop
        self.secondary_target = secondary_target
        self.sell_batch_size = sell_batch_size
        self.emergency_liquidity = emergency_liquidity
        self.care_animals = care_animals
        self.feed_buffer_days = feed_buffer_days
        self.day0_land = day0_land
        self.dynamic_elasticity = dynamic_elasticity

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
            market_inv = dict(market.get("inventory", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            goose_count = 0
            pasture_count = 0
            occupied_pastures = 0
            empty_pastures = []
            coop_count = 0
            occupied_coops = 0
            empty_coops = []
            melon_plants = 0
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
                                occupied_coops += 1
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
                                occupied_pastures += 1
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
                            if crop == "MELON": melon_plants += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            if crop == "MELON":
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # 2. Labor Hiring
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

            # 3. Land Expansion
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked < 2 and self.day0_land:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250:
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 500 and day <= 14:
                    orders.append(["BUY_LAND"])
                    money -= cost

            spendable = max(0.0, money - 25.0)

            # 4. Animal Procurement
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
                    cows_ordered += 1
                if needed_sheep > 0 and spendable >= 595 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    sheep_ordered += 1
                if needed_geese > 0 and spendable >= 350 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "GOOSE", 1])
                    spendable -= 300
                    money -= 300
                    geese_ordered += 1

            total_active_animals += cows_ordered + sheep_ordered + geese_ordered

            # 5. Feed Reserve
            feed_reserve_target = total_active_animals * (self.feed_buffer_days if day < 26 else 0)
            wheat_in_shed = shed.get("WHEAT", 0)
            if wheat_in_shed < feed_reserve_target and spendable >= 25 and len(orders) < 10:
                wheat_price = market_prices.get("WHEAT", 25)
                deficit = feed_reserve_target - wheat_in_shed
                max_affordable = int(spendable // max(1, wheat_price))
                to_buy = min(deficit, max_affordable, 15)
                if to_buy > 0:
                    orders.append(["BUY_PRODUCT", "WHEAT", to_buy])
                    spendable -= to_buy * wheat_price
                    money -= to_buy * wheat_price

            # 6. Emergency Liquidity Override
            if self.emergency_liquidity:
                feed_critical = (wheat_in_shed < total_active_animals * 2) if total_active_animals > 0 else False
                labor_critical = (hour == 0 and money < 20)
                if (feed_critical or labor_critical) and len(orders) < 10:
                    for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                        qty = shed.get(prod, 0)
                        if qty > 0 and len(orders) < 10:
                            orders.append(["SELL", prod, min(qty, 10)])
                            break

            # 7. Seed Purchasing
            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.target_melons and spendable >= 80 and len(orders) < 10:
                needed = self.target_melons - (melon_plants + seeds.get("MELON", 0))
                can_buy = min(needed, int(spendable // 80), 8)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy])
                    spendable -= can_buy * 80
                    money -= can_buy * 80

            if day >= 3 and day <= 26 and (seeds.get(self.secondary_crop, 0)) < self.secondary_target and spendable >= 40 and len(orders) < 10:
                needed = self.secondary_target - seeds.get(self.secondary_crop, 0)
                crop_seed_cost = CROPS[self.secondary_crop]["seed"]
                can_buy = min(needed, int(spendable // crop_seed_cost), 6)
                if can_buy > 0:
                    orders.append(["BUY_SEED", self.secondary_crop, can_buy])
                    spendable -= can_buy * crop_seed_cost
                    money -= can_buy * crop_seed_cost

            # 8. Liquidation Market Execution
            if step % 4 == 0 or step >= 680:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.sell_batch_size if step < 680 else 30)
                        orders.append(["SELL", prod, batch])

            # 9. 4-Pass Worker Dispatch
            unplaced_pasture_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            pastures_to_build = max(0, min(self.target_cows + self.target_sheep - pasture_count, unplaced_pasture_animals - len(empty_pastures)))
            unplaced_geese = geese_in_transit + geese_ordered
            coops_to_build = max(0, min(self.target_geese - coop_count, unplaced_geese - len(empty_coops)))

            worker_pos = [farmer_pos] + hands
            unassigned = list(range(len(worker_pos)))
            actions = [["PASS"] for _ in range(len(worker_pos))]
            assigned_pos = set()

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
                        continue
                    elif "animal" in t and t.get("animal"):
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            inv["WHEAT"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            if pos in unfed_animal_tiles:
                                unfed_animal_tiles.remove(pos)
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
                        for sc in ["MELON", "CARROT", "WHEAT"]:
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

            # Pass 3: Spatial Routing
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

            # Pass 4: Fallback & Chores
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

def wilson_ci(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(item):
    cand_params, opp_agent_or_path, seed, cand_is_p0 = item
    cand_inst = ParametricStrategy(**cand_params)
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    if cand_is_p0:
        agents = [cand_inst, opp_agent_or_path]
    else:
        agents = [opp_agent_or_path, cand_inst]
        
    try:
        env.run(agents)
        last = env.steps[-1]
        raw_r0 = float(last[0].reward or 0.0)
        raw_r1 = float(last[1].reward or 0.0)
        
        if cand_is_p0:
            r_cand, r_opp = raw_r0, raw_r1
        else:
            r_cand, r_opp = raw_r1, raw_r0
            
        margin = r_cand - r_opp
        win = 1.0 if r_cand > r_opp else (0.0 if r_opp > r_cand else 0.5)
        return {"seed": seed, "cand_is_p0": cand_is_p0, "r_cand": r_cand, "r_opp": r_opp, "margin": margin, "win": win}
    except Exception as e:
        return {"seed": seed, "cand_is_p0": cand_is_p0, "r_cand": 0.0, "r_opp": 0.0, "margin": 0.0, "win": 0.0, "error": str(e)}

def evaluate_strategy(cand_params, opp_agent_or_path, seeds, max_workers=6):
    tasks = []
    for s in seeds:
        tasks.append((cand_params, opp_agent_or_path, s, True))  # P0
        tasks.append((cand_params, opp_agent_or_path, s, False)) # P1
        
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())
            
    p0_res = [r for r in results if r["cand_is_p0"]]
    p1_res = [r for r in results if not r["cand_is_p0"]]
    
    p0_wins = sum(1 for r in p0_res if r["win"] == 1.0)
    p1_wins = sum(1 for r in p1_res if r["win"] == 1.0)
    total_wins = p0_wins + p1_wins
    total_games = len(results)
    
    p0_wr = (p0_wins / len(p0_res)) * 100.0 if p0_res else 0.0
    p1_wr = (p1_wins / len(p1_res)) * 100.0 if p1_res else 0.0
    pooled_wr = (total_wins / total_games) * 100.0 if total_games else 0.0
    w_low, w_high = wilson_ci(total_wins, total_games)
    
    margins = [r["margin"] for r in results]
    cand_cash = [r["r_cand"] for r in results]
    
    return {
        "name": cand_params.get("name", "Unknown"),
        "params": cand_params,
        "games": total_games,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "pooled_wr": pooled_wr,
        "ci_95": (w_low, w_high),
        "mean_margin": float(np.mean(margins)),
        "median_margin": float(np.median(margins)),
        "std_margin": float(np.std(margins)),
        "mean_cash": float(np.mean(cand_cash)),
        "worst_drawdown": float(np.min(margins)),
        "catastrophic": sum(1 for m in margins if m < -10000)
    }

if __name__ == "__main__":
    ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    seeds = [50000 + i for i in range(25)] # 50 matches per candidate
    
    candidates = [
        # 1. Baseline Control Equivalent
        {"name": "Control (8C/4S/15M/B14)", "target_cows": 8, "target_sheep": 4, "target_geese": 0, "target_melons": 15, "sell_batch_size": 14, "emergency_liquidity": False},
        # 2. Pure Crop
        {"name": "Pure Crop (0C/0S/25M/B14)", "target_cows": 0, "target_sheep": 0, "target_geese": 0, "target_melons": 25, "sell_batch_size": 14, "emergency_liquidity": False},
        # 3. Pure Livestock
        {"name": "Pure Livestock (10C/5S/0M/B14)", "target_cows": 10, "target_sheep": 5, "target_geese": 0, "target_melons": 0, "sell_batch_size": 14, "emergency_liquidity": False},
        # 4. Cow Heavy
        {"name": "Cow Heavy (10C/2S/15M/B24)", "target_cows": 10, "target_sheep": 2, "target_geese": 0, "target_melons": 15, "sell_batch_size": 24, "emergency_liquidity": True},
        # 5. Sheep Heavy
        {"name": "Sheep Heavy (4C/8S/15M/B24)", "target_cows": 4, "target_sheep": 8, "target_geese": 0, "target_melons": 15, "sell_batch_size": 24, "emergency_liquidity": True},
        # 6. Geese Fleet
        {"name": "Goose Fleet (6C/3S/4G/15M/B24)", "target_cows": 6, "target_sheep": 3, "target_geese": 4, "target_melons": 15, "sell_batch_size": 24, "emergency_liquidity": True},
        # 7. Batch 24 + Emergency (Synthesis)
        {"name": "Synthesis Peak (8C/4S/15M/B24+Emerg)", "target_cows": 8, "target_sheep": 4, "target_geese": 0, "target_melons": 15, "sell_batch_size": 24, "emergency_liquidity": True},
        # 8. High Melon Hybrid (8C/4S/20M/B24+Emerg)
        {"name": "High Melon (8C/4S/20M/B24+Emerg)", "target_cows": 8, "target_sheep": 4, "target_geese": 0, "target_melons": 20, "sell_batch_size": 24, "emergency_liquidity": True},
        # 9. Low Melon Fast Hybrid (6C/3S/10M/B24+Emerg)
        {"name": "Fast Hybrid (6C/3S/10M/B24+Emerg)", "target_cows": 6, "target_sheep": 3, "target_geese": 0, "target_melons": 10, "sell_batch_size": 24, "emergency_liquidity": True},
    ]
    
    print("=" * 95)
    print("STRATEGY GRID SEARCH: 9 STRATEGIC FAMILIES VS IMMUTABLE CONTROL (N=50 matches each)")
    print("=" * 95)
    
    scoreboard = []
    for cand in candidates:
        t0 = time.time()
        res = evaluate_strategy(cand, ctrl_path, seeds, max_workers=8)
        scoreboard.append(res)
        print(f"{res['name']:36s} | WR: {res['pooled_wr']:5.1f}% (P0:{res['p0_wr']:4.1f}% P1:{res['p1_wr']:4.1f}%) | CI: [{res['ci_95'][0]:4.1f}%, {res['ci_95'][1]:4.1f}%] | Margin: {res['mean_margin']:+8,.1f} | Cash: ${res['mean_cash']:7,.0f} ({time.time()-t0:.1f}s)")

