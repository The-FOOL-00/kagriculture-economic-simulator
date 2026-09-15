"""
Deep Head-to-Head Market, Yield, and Wealth Forensic Auditor
Runs matched games between Frozen V2 and CL-Economic-V1 (Seeds 5000-5099, alternating seats).
Captures:
- Full terminal wealth decomposition (inflows, outflows, net)
- Commodity volume and average realized prices
- Yield distribution (early vs batched strawberry harvests)
- Order slot priority and front-running price depression
- Unsold terminal assets (shed + worker pockets)
"""

import sys
import os
import json
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_agent

SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

def analyze_single_h2h(seed, cl_seat=0):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    if cl_seat == 0:
        agents = [cl_agent, v2_agent]
        p_cl, p_v2 = 0, 1
    else:
        agents = [v2_agent, cl_agent]
        p_cl, p_v2 = 1, 0

    env.run(agents)
    steps = env.steps
    total_steps = len(steps)

    players = [0, 1]
    
    # Revenue & Sales: item -> {"units": 0, "rev": 0.0, "prices": []}
    sales = {p: defaultdict(lambda: {"units": 0, "rev": 0.0, "prices": []}) for p in players}
    purchases = {p: defaultdict(lambda: {"units": 0, "cost": 0.0}) for p in players}
    
    # Harvests: crop -> {"total_yield": 0, "harvest_events": 0, "yield_counts": defaultdict(int), "fertilized_events": 0}
    harvests = {p: defaultdict(lambda: {"total_yield": 0, "harvest_events": 0, "yield_counts": defaultdict(int), "fertilized_events": 0}) for p in players}
    
    # Tasks: category -> turns
    task_counts = {p: defaultdict(int) for p in players}
    
    # Front-running: item -> {"collision_events": 0, "cl_price_depressed_sum": 0.0, "v2_first_count": 0, "cl_first_count": 0}
    front_run_stats = defaultdict(lambda: {"collision_events": 0, "cl_price_depressed_sum": 0.0, "v2_first_count": 0, "cl_first_count": 0})
    
    # Step-by-step trace
    for s_idx in range(1, total_steps):
        prev_obs_0 = steps[s_idx - 1][0]["observation"]
        prev_obs_1 = steps[s_idx - 1][1]["observation"]
        
        act_0 = steps[s_idx][0].get("action") or {}
        act_1 = steps[s_idx][1].get("action") or {}
        acts = {0: act_0, 1: act_1}
        
        m_prices = prev_obs_0.get("market", {}).get("prices", {})
        
        # Track worker task types for both players
        for p in players:
            farm_prev = steps[s_idx - 1][p]["observation"]["farms"][p]
            f_act = acts[p].get("farmer") or ["PASS"]
            h_acts = acts[p].get("hands") or []
            for w_act in [f_act] + h_acts:
                cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else (w_act if isinstance(w_act, str) else "PASS")
                if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                    task_counts[p]["MOVEMENT"] += 1
                elif cmd in ("WATER", "WATER_CROP"):
                    task_counts[p]["WATER"] += 1
                elif cmd in ("HARVEST", "HARVEST_CROP"):
                    task_counts[p]["HARVEST"] += 1
                elif cmd in ("TILL", "PLANT"):
                    task_counts[p]["PLANT"] += 1
                elif cmd in ("BUILD_PASTURE", "FEED", "BRUSH", "COLLECT_MILK", "COLLECT_WOOL", "COLLECT_EGG"):
                    task_counts[p]["LIVESTOCK"] += 1
                elif cmd in ("DROP", "PICKUP"):
                    task_counts[p]["SHED"] += 1
                elif cmd == "PASS":
                    task_counts[p]["PASS"] += 1
                else:
                    task_counts[p]["OTHER"] += 1

            # Harvest tile tracking (yield size, crop, fertilization)
            farm_curr = steps[s_idx][p]["observation"]["farms"][p]
            p_tiles = farm_prev.get("tiles") or []
            c_tiles = farm_curr.get("tiles") or []
            for r in range(len(p_tiles)):
                for c in range(len(p_tiles[r])):
                    pt = p_tiles[r][c] if isinstance(p_tiles[r][c], dict) else {}
                    ct = c_tiles[r][c] if isinstance(c_tiles[r][c], dict) else {}
                    if pt.get("crop") and int(pt.get("yield_units", 0) or 0) > 0:
                        p_y = int(pt.get("yield_units", 0) or 0)
                        c_y = int(ct.get("yield_units", 0) or 0) if ct.get("crop") == pt.get("crop") else 0
                        if not ct.get("crop") or c_y < p_y:
                            harv_y = p_y - c_y
                            crop = pt.get("crop")
                            is_fert = pt.get("fertilized", False)
                            harvests[p][crop]["total_yield"] += harv_y
                            harvests[p][crop]["harvest_events"] += 1
                            harvests[p][crop]["yield_counts"][harv_y] += 1
                            if is_fert:
                                harvests[p][crop]["fertilized_events"] += 1

        # Simulate interleaved market order resolution
        m_orders_0 = acts[0].get("market") or []
        m_orders_1 = acts[1].get("market") or []
        max_orders = max(len(m_orders_0), len(m_orders_1))
        
        interleaved = []
        for i in range(max_orders):
            if i < len(m_orders_0):
                interleaved.append((0, i, m_orders_0[i]))
            if i < len(m_orders_1):
                interleaved.append((1, i, m_orders_1[i]))
                
        sells_in_step = {0: [], 1: []}
        for p, slot_idx, order in interleaved:
            if not isinstance(order, list) or len(order) == 0: continue
            cmd = order[0]
            if cmd == "SELL":
                item = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                sells_in_step[p].append((item, qty, slot_idx))
                price = float(m_prices.get(item, BASE_PRICES.get(item, 100)))
                sales[p][item]["units"] += qty
                sales[p][item]["rev"] += price * qty
                sales[p][item]["prices"].append(price)
            elif cmd == "BUY_PRODUCT":
                item = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                price = float(m_prices.get(item, 30))
                purchases[p][item]["units"] += qty
                purchases[p][item]["cost"] += price * qty
            elif cmd == "BUY_SEED":
                stype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                cost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(stype, 10) * qty
                purchases[p][f"SEED_{stype}"]["units"] += qty
                purchases[p][f"SEED_{stype}"]["cost"] += cost
            elif cmd == "BUY_ANIMAL":
                atype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                cost = {"COW": 400, "SHEEP": 500, "GOOSE": 200}.get(atype, 400) * qty
                purchases[p][atype]["units"] += qty
                purchases[p][atype]["cost"] += cost
            elif cmd == "HIRE":
                purchases[p]["HIRE"]["units"] += 1
            elif cmd == "BUY_LAND":
                purchases[p]["BUY_LAND"]["units"] += 1

        v2_sells = sells_in_step[p_v2]
        cl_sells = sells_in_step[p_cl]
        for v_item, v_qty, v_slot in v2_sells:
            for c_item, c_qty, c_slot in cl_sells:
                if v_item == c_item:
                    front_run_stats[v_item]["collision_events"] += 1
                    v_prio = v_slot * 2 + p_v2
                    c_prio = c_slot * 2 + p_cl
                    if v_prio < c_prio:
                        front_run_stats[v_item]["v2_first_count"] += 1
                    else:
                        front_run_stats[v_item]["cl_first_count"] += 1

    final_obs_0 = steps[-1][0]["observation"]
    final_obs_1 = steps[-1][1]["observation"]
    
    final_rewards = {
        0: float(steps[-1][0].get("reward") or 0.0),
        1: float(steps[-1][1].get("reward") or 0.0)
    }
    
    terminal_unsold = {0: defaultdict(int), 1: defaultdict(int)}
    terminal_unsold_val = {0: 0.0, 1: 0.0}
    final_m_prices = final_obs_0.get("market", {}).get("prices", {})
    
    for p in players:
        p_obs = steps[-1][p]["observation"]
        p_shed = (p_obs.get("private") or {}).get("shed") or {}
        p_invs = (p_obs.get("private") or {}).get("inventories") or []
        for it, q in p_shed.items():
            if int(q or 0) > 0:
                terminal_unsold[p][f"SHED_{it}"] += int(q)
                p_price = float(final_m_prices.get(it, BASE_PRICES.get(it, 50)))
                terminal_unsold_val[p] += int(q) * p_price
        for inv in p_invs:
            if isinstance(inv, dict):
                for it, q in inv.items():
                    if int(q or 0) > 0:
                        terminal_unsold[p][f"POCKET_{it}"] += int(q)
                        p_price = float(final_m_prices.get(it, BASE_PRICES.get(it, 50)))
                        terminal_unsold_val[p] += int(q) * p_price

    cl_reward = final_rewards[p_cl]
    v2_reward = final_rewards[p_v2]
    
    return {
        "seed": seed,
        "cl_seat": cl_seat,
        "cl_reward": cl_reward,
        "v2_reward": v2_reward,
        "margin": cl_reward - v2_reward,
        "cl_sales": {k: {"units": v["units"], "rev": v["rev"], "avg_price": v["rev"]/v["units"] if v["units"] > 0 else 0.0} for k, v in sales[p_cl].items()},
        "v2_sales": {k: {"units": v["units"], "rev": v["rev"], "avg_price": v["rev"]/v["units"] if v["units"] > 0 else 0.0} for k, v in sales[p_v2].items()},
        "cl_purchases": {k: {"units": v["units"], "cost": v["cost"]} for k, v in purchases[p_cl].items()},
        "v2_purchases": {k: {"units": v["units"], "cost": v["cost"]} for k, v in purchases[p_v2].items()},
        "cl_harvests": {k: {"total_yield": v["total_yield"], "harvest_events": v["harvest_events"], "yield_1_count": v["yield_counts"][1], "yield_2plus_count": sum(c for y, c in v["yield_counts"].items() if y >= 2), "fertilized_events": v["fertilized_events"]} for k, v in harvests[p_cl].items()},
        "v2_harvests": {k: {"total_yield": v["total_yield"], "harvest_events": v["harvest_events"], "yield_1_count": v["yield_counts"][1], "yield_2plus_count": sum(c for y, c in v["yield_counts"].items() if y >= 2), "fertilized_events": v["fertilized_events"]} for k, v in harvests[p_v2].items()},
        "cl_tasks": dict(task_counts[p_cl]),
        "v2_tasks": dict(task_counts[p_v2]),
        "cl_unsold_val": terminal_unsold_val[p_cl],
        "v2_unsold_val": terminal_unsold_val[p_v2],
        "cl_unsold": dict(terminal_unsold[p_cl]),
        "v2_unsold": dict(terminal_unsold[p_v2]),
        "front_run_stats": {k: dict(v) for k, v in front_run_stats.items()}
    }

def run_forensic_suite(seeds, max_workers=10):
    tasks = []
    for i, s in enumerate(seeds):
        cl_seat = i % 2
        tasks.append((s, cl_seat))
        
    print(f"Starting {len(seeds)}-match Head-to-Head forensic audit (Frozen V2 vs CL-Economic-V1)...")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_single_h2h, s, seat): (s, seat) for s, seat in tasks}
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            if len(results) % 20 == 0 or len(results) == len(seeds):
                print(f"  Completed {len(results)}/{len(seeds)} matches in {time.time()-t0:.1f}s...")
                
    elapsed = time.time() - t0
    print(f"Completed all {len(results)} matches in {elapsed:.1f}s.")
    return results

if __name__ == "__main__":
    test_res = analyze_single_h2h(seed=5000, cl_seat=0)
    print("Test run on Seed 5000 completed successfully:")
    print(f"  CL Reward: ${test_res['cl_reward']:,.2f}")
    print(f"  V2 Reward: ${test_res['v2_reward']:,.2f}")
    print(f"  Net Margin: ${test_res['margin']:,.2f}")
    print("  CL Sales:", {k: v['units'] for k, v in test_res['cl_sales'].items()})
    print("  V2 Sales:", {k: v['units'] for k, v in test_res['v2_sales'].items()})
