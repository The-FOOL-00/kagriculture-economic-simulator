import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1, CROPS_DEF
import candidates.slot2_aethel_refined_v2 as v2_mod

def audit_melon_plantings_deep(seeds=list(range(1000, 1010))):
    print("Reconstructing every melon planting for CL and V2 across Seeds 1000-1009...")
    
    cl_melon_records = []
    v2_melon_records = []
    
    # Engine rules:
    # MELON: first_yield_day: 10, max_yield_day: 12, max_yield: 6.
    # Episode ends at step 719 (Day 29 hour 23).
    # Step where first yield is generated:
    # A melon planted on step s (day d = s // 24) receives daily refresh at each day boundary.
    # After 10 days of growth (planted_day + 10), its yield units begin accumulating.
    # If planted_day + 10 >= 30, it NEVER generates yield before step 720!
    # That is, planted_day >= 20 means planted_day + 10 >= 30 -> 0 yields possible!
    
    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}
        
        # 1. Run CL
        env_cl = kaggle_environments.make("kaggriculture", configuration=cfg)
        cl_inst = ClosedLoopEconomicV1()
        env_cl.run([cl_inst, "starter"])
        
        # 2. Run V2
        env_v2 = kaggle_environments.make("kaggriculture", configuration=cfg)
        env_v2.run([v2_mod.agent, "starter"])
        
        for agent_label, env_inst, record_list in [("CL", env_cl, cl_melon_records), ("V2", env_v2, v2_melon_records)]:
            steps = env_inst.steps
            
            # We track tiles over time to inspect prior crop, watering, and yield
            active_melons = {} # coord: { details }
            
            for step_idx in range(1, len(steps)):
                day = step_idx // 24
                hour = step_idx % 24
                prev_f = steps[step_idx - 1][0]["observation"]["farms"][0]
                act = steps[step_idx][0].get("action") or {}
                all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
                workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
                money = float(prev_f.get("money") or 0.0)
                tiles = prev_f["tiles"]
                
                # Check actions for PLANT MELON, WATER on melon, HARVEST on melon
                for w_idx, a in enumerate(all_acts):
                    if not a: continue
                    op = a[0]
                    pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                    x, y = pos
                    
                    if op == "PLANT" and len(a) > 1 and a[1] == "MELON":
                        # Determine previous tile state
                        prev_tile = tiles[y][x]
                        prev_crop = None
                        fertilized = False
                        if isinstance(prev_tile, dict):
                            prev_crop = prev_tile.get("crop")
                            fertilized = (prev_tile.get("fertilized_until_day", -1) >= day)
                            
                        # First possible productive harvest step
                        # Melon needs first_yield_day (10 days).
                        first_harvest_day = day + 10
                        is_late = (first_harvest_day >= 30)
                        
                        rec = {
                            "seed": s,
                            "agent": agent_label,
                            "step": step_idx,
                            "day": day,
                            "hour": hour,
                            "coord": (x, y),
                            "money_at_plant": money,
                            "workers_total": len(workers),
                            "prev_crop": prev_crop,
                            "fertilized": fertilized,
                            "expected_first_yield_day": first_harvest_day,
                            "is_late": is_late,
                            "water_actions": 0,
                            "harvest_actions": 0,
                            "harvested_yield": 0,
                            "final_yield_on_tile": 0
                        }
                        active_melons[(x, y)] = rec
                        record_list.append(rec)
                        
                    elif op == "WATER":
                        if pos in active_melons:
                            active_melons[pos]["water_actions"] += 1
                            
                    elif op == "HARVEST":
                        t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
                        if isinstance(t, dict) and t.get("crop") == "MELON":
                            yu = int(t.get("yield_units", 0) or 0)
                            if pos in active_melons:
                                active_melons[pos]["harvest_actions"] += 1
                                active_melons[pos]["harvested_yield"] += yu

            # Final state check for all melons
            final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
            for coord, rec in active_melons.items():
                x, y = coord
                ft = final_tiles[y][x]
                if isinstance(ft, dict) and ft.get("crop") == "MELON":
                    rec["final_yield_on_tile"] = int(ft.get("yield_units", 0) or 0)

    return cl_melon_records, v2_melon_records

# Clean Late-Melon Cutoff Candidate
class CLLateMelonCutoff(ClosedLoopEconomicV1):
    def __init__(self, cutoff_day=18):
        super().__init__()
        self.cutoff_day = cutoff_day

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []
        if step == 0:
            return super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot

        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(12, int(n_animals * 1.5))
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, 100) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(12, int(n_animals * 1.5))
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s

        # LATE MELON CUTOFF: Strictly enforce day <= cutoff_day (e.g. Day 18)
        # Because melon needs 10 days to first yield, planting at day >= 20 reaches maturity at day 30 (after game ends!)
        # Day 18 reaches first yield day at Day 28, yielding on Days 28 and 29.
        if hour == 0 and 4 <= day <= self.cutoff_day and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (11 if day < 12 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        if hour == 0 and 4 <= day <= 20 and len(orders) < 8:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        else: target_hands = 11

        cur_h = hired
        budget = money
        while cur_h < target_hands and len(orders) < 10:
            from candidates.candidate_cl_economic_v1 import _fib
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Also enforce planting cutoff in _scan_field so existing seeds aren't planted if day > cutoff_day
        if day > self.cutoff_day:
            res["plant_m"] = []
        return res

def run_counterfactual_late_melon(args):
    arm, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    if arm == "BASELINE":
        agent_inst = ClosedLoopEconomicV1()
    elif arm == "CUTOFF_D18":
        agent_inst = CLLateMelonCutoff(cutoff_day=18)
    elif arm == "CUTOFF_D17":
        agent_inst = CLLateMelonCutoff(cutoff_day=17)
    elif arm == "CUTOFF_D19":
        agent_inst = CLLateMelonCutoff(cutoff_day=19)
    else:
        raise ValueError(f"Unknown {arm}")
        
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvs = 0
    total_plants = 0
    total_moves = 0
    total_waters = 0
    melon_plants = 0
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a: continue
            op = a[0]
            if op == "HARVEST":
                total_harvs += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    yu = int(t.get("yield_units", 0) or 0)
                    if t.get("kind") == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif t.get("kind") == "PASTURE": harvest_counts[t.get("animal")] += yu
            elif op == "PLANT":
                total_plants += 1
                if len(a) > 1 and a[1] == "MELON": melon_plants += 1
            elif op == "WATER":
                total_waters += 1
            elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    terminal_cash = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    
    return {
        "arm": arm,
        "seed": seed,
        "reward": reward,
        "terminal_cash": terminal_cash,
        "harvests": total_harvs,
        "plants": total_plants,
        "melon_plants": melon_plants,
        "waters": total_waters,
        "moves": total_moves,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "milk": harvest_counts.get("COW", 0)
    }

if __name__ == "__main__":
    # 1. Forensic Melon Reconstruction
    cl_melons, v2_melons = audit_melon_plantings_deep()
    
    # Analyze CL late melons
    cl_late = [m for m in cl_melons if m["is_late"]]
    v2_late = [m for m in v2_melons if m["is_late"]]
    
    print("\n" + "="*80)
    print("SECTION 4 & 6: LATE-MELON FORENSIC AUDIT")
    print("="*80)
    print(f"Total CL Melon Plantings across 10 seeds: {len(cl_melons)} (Mean: {len(cl_melons)/10:.1f})")
    print(f"CL LATE Melon Plantings (planted day >= 20): {len(cl_late)} (Mean: {len(cl_late)/10:.1f})")
    print(f"Total V2 Melon Plantings across 10 seeds: {len(v2_melons)} (Mean: {len(v2_melons)/10:.1f})")
    print(f"V2 LATE Melon Plantings (planted day >= 20): {len(v2_late)} (Mean: {len(v2_late)/10:.1f})")
    
    # Verify the $1,920 claim
    late_seeds_bought = len(cl_late)
    late_capital_spent = late_seeds_bought * 80 # seed cost $80
    late_harvested_yield = sum(m["harvested_yield"] for m in cl_late)
    late_final_yield = sum(m["final_yield_on_tile"] for m in cl_late)
    late_water_actions = sum(m["water_actions"] for m in cl_late)
    
    print("\n--- Testing the $1,920 Claim ---")
    print(f"1. Exactly {len(cl_late)} late melon plantings exist across Seeds 1000-1009.")
    print(f"2. Actual melon seed cost is $80. Total capital spent: {len(cl_late)} x $80 = ${late_capital_spent}.")
    print(f"3. Actual yield harvested from late melons: {late_harvested_yield} units.")
    print(f"4. Final unharvested yield on late melon tiles at Step 719: {late_final_yield} units.")
    print(f"5. Total worker watering actions spent on late melons: {late_water_actions} actions.")
    
    # 2. Counterfactual Intervention Study
    arms = ["BASELINE", "CUTOFF_D17", "CUTOFF_D18", "CUTOFF_D19"]
    seeds = list(range(1000, 1010))
    cf_tasks = [(arm, s) for arm in arms for s in seeds]
    
    print(f"\nRunning Late-Melon Counterfactual Interventions ({len(cf_tasks)} matches)...")
    cf_results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_counterfactual_late_melon, t) for t in cf_tasks]
        for f in as_completed(futs):
            res = f.result()
            cf_results[res["arm"]].append(res)
            
    with open("scratch/audit_late_melon_counterfactual_results.json", "w") as f:
        json.dump({k: v for k, v in cf_results.items()}, f, indent=2)
        
    print("\n" + "="*110)
    print(f"{'ARM':<16} | {'Reward ($)':<16} | {'Delta ($)':<12} | {'Melon Plants':<13} | {'Melon (u)':<10} | {'Straw (u)':<10} | {'Waters':<8} | {'Moves':<8}")
    print("-" * 110)
    
    base_rew = np.mean([x["reward"] for x in cf_results["BASELINE"]])
    for arm in arms:
        lst = cf_results[arm]
        lst.sort(key=lambda x: x["seed"])
        rews = [x["reward"] for x in lst]
        m_rew = float(np.mean(rews))
        std_rew = float(np.std(rews))
        ci95 = 1.96 * std_rew / np.sqrt(len(rews))
        m_plants = float(np.mean([x["melon_plants"] for x in lst]))
        m_melon = float(np.mean([x["melon"] for x in lst]))
        m_straw = float(np.mean([x["straw"] for x in lst]))
        m_waters = float(np.mean([x["waters"] for x in lst]))
        m_moves = float(np.mean([x["moves"] for x in lst]))
        delta = m_rew - base_rew
        print(f"{arm:<16} | ${m_rew:10.2f} ± ${ci95:5.0f} | {delta:+10.2f} | {m_plants:13.1f} | {m_melon:10.1f} | {m_straw:10.1f} | {m_waters:8.1f} | {m_moves:8.1f}")
