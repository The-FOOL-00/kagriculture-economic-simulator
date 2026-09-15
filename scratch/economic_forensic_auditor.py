"""
Economic Forensic Auditor & Terminal Wealth Decomposition
Post-hoc analysis of matched game traces to inspect every economic decision:
Hiring, Crop Portfolio, Livestock, Feed, Inventory, Realized Prices, Labor Allocation.
"""

import sys
import os
import json
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_coordinated_v1 import agent as cl_agent

SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def analyze_match_trace(agent_fn, agent_name, seed=42, opponent="starter", seat=0):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    if seat == 0:
        agents = [agent_fn, opponent]
    else:
        agents = [opponent, agent_fn]
        
    env.run(agents)
    steps = env.steps
    total_steps = len(steps)
    p = seat
    
    # Forensic Accounting Structures
    inflows = defaultdict(float) # Item -> money gained
    outflows = defaultdict(float) # Category -> money spent
    
    order_counts = defaultdict(int) # (ORDER_TYPE, ITEM) -> count
    units_sold = defaultdict(int) # Item -> units
    units_bought = defaultdict(int) # Item -> units
    
    crops_planted = defaultdict(int) # Crop -> count
    crops_harvested = defaultdict(int) # Crop -> count
    
    worker_history = []
    cash_history = []
    
    # Task categories for hands & farmer
    task_categories = defaultdict(int) # category -> turns spent
    
    # Step-by-step analysis
    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx - 1][p]["observation"]
        curr_obs = steps[s_idx][p]["observation"]
        
        prev_farm = prev_obs["farms"][p]
        curr_farm = curr_obs["farms"][p]
        
        prev_money = float(prev_farm["money"])
        curr_money = float(curr_farm["money"])
        delta_money = curr_money - prev_money
        
        prev_workers = [tuple(prev_farm["farmer"])] + [tuple(h) for h in prev_farm["hands"]]
        curr_workers = [tuple(curr_farm["farmer"])] + [tuple(h) for h in curr_farm["hands"]]
        
        worker_history.append(len(curr_workers))
        cash_history.append(curr_money)
        
        # Actions taken in step s_idx
        # In kaggle_environments, step[s_idx] contains the action chosen in step s_idx-1
        act = steps[s_idx][p].get("action") or {}
        market_orders = act.get("market") or []
        
        # Classify worker actions
        farmer_act = act.get("farmer") or ["PASS"]
        hands_acts = act.get("hands") or []
        
        for w_act in [farmer_act] + hands_acts:
            cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else (w_act if isinstance(w_act, str) else "PASS")
            if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                task_categories["MOVEMENT"] += 1
            elif cmd in ("WATER", "WATER_CROP"):
                task_categories["WATER"] += 1
            elif cmd in ("HARVEST", "HARVEST_CROP"):
                task_categories["HARVEST"] += 1
            elif cmd in ("TILL", "PLANT"):
                task_categories["PLANTING"] += 1
            elif cmd in ("BUILD_PASTURE", "FEED", "BRUSH", "COLLECT_MILK", "COLLECT_WOOL", "COLLECT_EGG"):
                task_categories["LIVESTOCK_CARE"] += 1
            elif cmd in ("DROP", "PICKUP"):
                task_categories["SHED_LOGISTICS"] += 1
            elif cmd == "PASS":
                task_categories["PASS"] += 1
            else:
                task_categories["OTHER_PROD"] += 1

        # Tile state diff for plant/harvest
        p_tiles = prev_farm["tiles"]
        c_tiles = curr_farm["tiles"]
        for r in range(len(p_tiles)):
            for c in range(len(p_tiles[r])):
                pt = p_tiles[r][c] if isinstance(p_tiles[r][c], dict) else {}
                ct = c_tiles[r][c] if isinstance(c_tiles[r][c], dict) else {}
                if not pt.get("crop") and ct.get("crop"):
                    crops_planted[ct["crop"]] += 1
                if pt.get("crop") and not ct.get("crop") and int(pt.get("yield_units", 0) or 0) > 0:
                    crops_harvested[pt["crop"]] += 1
                    
        # Market order accounting
        prices = prev_obs.get("market", {}).get("prices", {})
        # Note: if delta_money > 0, sales occurred
        # If delta_money < 0, purchases/hires occurred
        for order in market_orders:
            if not isinstance(order, list) or len(order) == 0: continue
            cmd = order[0]
            if cmd == "HIRE":
                order_counts["HIRE"] += 1
            elif cmd == "BUY_LAND":
                order_counts["BUY_LAND"] += 1
                outflows["LAND"] += 1000 # approximation
            elif cmd == "BUY_ANIMAL":
                atype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                order_counts[f"BUY_ANIMAL_{atype}"] += qty
                units_bought[atype] += qty
                cost = 400 * qty if atype == "COW" else (500 * qty if atype == "SHEEP" else 200 * qty)
                outflows["ANIMALS"] += cost
            elif cmd == "BUY_SEED":
                stype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                order_counts[f"BUY_SEED_{stype}"] += qty
                units_bought[f"SEED_{stype}"] += qty
                seed_cost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(stype, 10) * qty
                outflows["SEEDS"] += seed_cost
            elif cmd == "BUY_PRODUCT":
                ptype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                order_counts[f"BUY_PRODUCT_{ptype}"] += qty
                units_bought[ptype] += qty
                p_cost = float(prices.get(ptype, 30)) * qty
                if ptype == "WHEAT":
                    outflows["FEED"] += p_cost
                else:
                    outflows["OTHER_INPUTS"] += p_cost
            elif cmd == "SELL":
                stype = order[1]
                qty = int(order[2]) if len(order) > 2 else 1
                order_counts[f"SELL_{stype}"] += qty
                units_sold[stype] += qty
                rev = float(prices.get(stype, 1)) * qty
                inflows[stype] += rev

    final_obs = steps[-1][p]["observation"]
    final_farm = final_obs["farms"][p]
    final_shed = dict(final_obs["private"]["shed"])
    final_money = float(final_farm["money"])
    final_reward = float(steps[-1][p].get("reward") or 0.0)
    
    # Calculate gross inflows/outflows from money trajectory
    gross_cash_inflow = sum(max(0, cash_history[i] - cash_history[i-1]) for i in range(1, len(cash_history)))
    gross_cash_outflow = sum(max(0, cash_history[i-1] - cash_history[i]) for i in range(1, len(cash_history)))
    
    return {
        "agent": agent_name,
        "seed": seed,
        "seat": seat,
        "final_reward": final_reward,
        "final_money": final_money,
        "gross_cash_inflow": gross_cash_inflow,
        "gross_cash_outflow": gross_cash_outflow,
        "net_gain": final_reward - 3000.0,
        "final_workers": len(final_farm["hands"]) + 1,
        "inflows": dict(inflows),
        "outflows": dict(outflows),
        "order_counts": dict(order_counts),
        "units_sold": dict(units_sold),
        "units_bought": dict(units_bought),
        "crops_planted": dict(crops_planted),
        "crops_harvested": dict(crops_harvested),
        "task_categories": dict(task_categories),
        "final_shed": final_shed,
        "mean_workers": float(np.mean(worker_history)),
        "max_workers": int(np.max(worker_history)),
    }

def print_forensic_comparison(v2, cl):
    print("\n" + "=" * 90)
    print(f"TERMINAL WEALTH DECOMPOSITION & ECONOMIC FORENSICS (Seed {v2['seed']})")
    print("=" * 90)
    print(f"{'METRIC':<35} | {'FROZEN V2':<22} | {'CL-COORDINATED-V1':<22} | {'DELTA (V2 - CL)':<15}")
    print("-" * 90)
    print(f"{'Final Reward / Wealth':<35} | ${v2['final_reward']:14,.2f} | ${cl['final_reward']:14,.2f} | +${v2['final_reward'] - cl['final_reward']:12,.2f}")
    print(f"{'Gross Cash Inflows':<35} | ${v2['gross_cash_inflow']:14,.2f} | ${cl['gross_cash_inflow']:14,.2f} | +${v2['gross_cash_inflow'] - cl['gross_cash_inflow']:12,.2f}")
    print(f"{'Gross Cash Outflows':<35} | ${v2['gross_cash_outflow']:14,.2f} | ${cl['gross_cash_outflow']:14,.2f} | +${v2['gross_cash_outflow'] - cl['gross_cash_outflow']:12,.2f}")
    print(f"{'Starting Capital':<35} | ${3000.0:14,.2f} | ${3000.0:14,.2f} | $0.00")
    print(f"{'Net Capital Lift':<35} | ${v2['net_gain']:14,.2f} | ${cl['net_gain']:14,.2f} | +${v2['net_gain'] - cl['net_gain']:12,.2f}")
    print(f"{'Final Worker Count (Hands+1)':<35} | {v2['final_workers']:14d} | {cl['final_workers']:14d} | {v2['final_workers'] - cl['final_workers']:14d}")
    print(f"{'Average Active Workers':<35} | {v2['mean_workers']:14.1f} | {cl['mean_workers']:14.1f} | {v2['mean_workers'] - cl['mean_workers']:14.1f}")
    print("-" * 90)
    
    print("\n--- REVENUE SOURCES (EST. CASH FROM SALES) ---")
    all_items = sorted(set(list(v2["inflows"].keys()) + list(cl["inflows"].keys())))
    v2_tot_rev = sum(v2["inflows"].values())
    cl_tot_rev = sum(cl["inflows"].values())
    for item in all_items:
        v_rev = v2["inflows"].get(item, 0.0)
        c_rev = cl["inflows"].get(item, 0.0)
        v_u = v2["units_sold"].get(item, 0)
        c_u = cl["units_sold"].get(item, 0)
        print(f"{item:<15} | V2: {v_u:4d} units (${v_rev:10,.1f}) | CL: {c_u:4d} units (${c_rev:10,.1f}) | Delta: +${v_rev - c_rev:10,.1f}")
    print(f"{'TOTAL SALES EST':<15} | V2:      ${v2_tot_rev:10,.1f}  | CL:      ${cl_tot_rev:10,.1f}  | Delta: +${v2_tot_rev - cl_tot_rev:10,.1f}")
    
    print("\n--- CROPS PLANTED & HARVESTED ---")
    all_crops = sorted(set(list(v2["crops_planted"].keys()) + list(cl["crops_planted"].keys())))
    for crop in all_crops:
        v_p = v2["crops_planted"].get(crop, 0)
        c_p = cl["crops_planted"].get(crop, 0)
        v_h = v2["crops_harvested"].get(crop, 0)
        c_h = cl["crops_harvested"].get(crop, 0)
        print(f"{crop:<15} | V2: Planted {v_p:3d}, Harvd {v_h:3d} | CL: Planted {c_p:3d}, Harvd {c_h:3d} | Net Harvd Delta: {v_h - c_h:3d}")
        
    print("\n--- PURCHASES / CAPITAL ALLOCATION ---")
    all_buys = sorted(set(list(v2["units_bought"].keys()) + list(cl["units_bought"].keys())))
    for b in all_buys:
        v_u = v2["units_bought"].get(b, 0)
        c_u = cl["units_bought"].get(b, 0)
        print(f"{b:<20} | V2: Bought {v_u:4d} units | CL: Bought {c_u:4d} units | Delta: {v_u - c_u:4d}")
        
    print("\n--- LABOR ALLOCATION (TURNS SPENT BY TASK) ---")
    all_tasks = sorted(set(list(v2["task_categories"].keys()) + list(cl["task_categories"].keys())))
    for t in all_tasks:
        v_t = v2["task_categories"].get(t, 0)
        c_t = cl["task_categories"].get(t, 0)
        print(f"{t:<20} | V2: {v_t:5d} turns ({v_t/720/v2['mean_workers']*100:4.1f}%) | CL: {c_t:5d} turns ({c_t/720/cl['mean_workers']*100:4.1f}%) | Delta: {v_t - c_t:5d}")
        
    print("\n--- UNSOLD / TERMINAL SHED INVENTORY ---")
    all_shed = sorted(set(list(v2["final_shed"].keys()) + list(cl["final_shed"].keys())))
    for item in all_shed:
        v_s = v2["final_shed"].get(item, 0)
        c_s = cl["final_shed"].get(item, 0)
        if v_s > 0 or c_s > 0:
            print(f"{item:<15} | V2 Unsold: {v_s:4d} units | CL Unsold: {c_s:4d} units | Delta: {v_s - c_s:4d}")
    print("=" * 90)

if __name__ == "__main__":
    v2_res = analyze_match_trace(v2_agent, "Frozen V2", seed=42)
    cl_res = analyze_match_trace(cl_agent, "CL-Coordinated-V1", seed=42)
    print_forensic_comparison(v2_res, cl_res)
