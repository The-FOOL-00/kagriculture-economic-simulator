"""
Reconcile H2H Accounting Discrepancy & Counterfactual Market Analysis
====================================================================
Detailed step-by-step transaction recorder and counterfactual auditor for:
1. Frozen V2 vs CL-Economic-V1 (100 Seeds 5000-5099, alternating seats)
2. Frozen V2 vs CL-Temporal-V3 (100 Seeds 5000-5099, alternating seats)
3. Frozen V2 vs CL-Temporal-V2 (100 Seeds 5000-5099, alternating seats)

Tracks:
- Every market order and individual unit sold/bought
- Pre-order and post-order inventory
- Realized price vs Base price vs Pre-V2 price vs Priority-swapped price
- Full 9-component economic wealth decomposition:
  1. Production quantity gap
  2. Production timing gap
  3. Input-cost gap
  4. Labor-cost gap
  5. Movement/logistics gap
  6. Market price gap (macro volume)
  7. Order-priority gap (micro slot front-running)
  8. Terminal inventory gap
  9. Other / residual
"""

import sys
import os
import json
import time
import math
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as k_env
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_econ_agent
from candidates.candidate_cl_temporal_v2 import agent as cl_temp2_agent
from candidates.candidate_cl_temporal_v3 import agent as cl_temp3_agent

MARKET_PARAMS = k_env.MARKET_PARAMS
BASE_PRICES = {k: v["base"] for k, v in MARKET_PARAMS.items()}

def calc_market_price(item, inventory):
    return k_env.market_price(item, inventory, MARKET_PARAMS)

def run_audited_match(seed, cand_module_name, cand_seat):
    mod = __import__(cand_module_name, fromlist=["agent"])
    cand_agent = mod.agent
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    if cand_seat == 0:
        agents = [cand_agent, v2_agent]
        p_cand, p_v2 = 0, 1
    else:
        agents = [v2_agent, cand_agent]
        p_cand, p_v2 = 1, 0
        
    env.run(agents)
    steps = env.steps
    total_steps = len(steps)
    
    sales_units = {0: defaultdict(int), 1: defaultdict(int)}
    sales_rev_realized = {0: defaultdict(float), 1: defaultdict(float)}
    sales_rev_base = {0: defaultdict(float), 1: defaultdict(float)}
    
    cf_rev_cand = {"realized": 0.0, "pre_v2": 0.0, "base": 0.0, "prio_swapped": 0.0}
    
    purchases_cost = {0: defaultdict(float), 1: defaultdict(float)}
    hiring_cost = {0: 0.0, 1: 0.0}
    land_cost = {0: 0.0, 1: 0.0}
    
    task_counts = {0: defaultdict(int), 1: defaultdict(int)}
    
    same_step_same_item_collisions = 0
    v2_earlier_slot_collisions = 0
    cand_earlier_slot_collisions = 0
    same_slot_collisions = 0
    cand_priority_loss_dollars = 0.0
    
    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        
        m_inv_start = dict(prev_obs["market"]["inventory"])
        act_0 = steps[s_idx][0].get("action") or {}
        act_1 = steps[s_idx][1].get("action") or {}
        
        for p, act in [(0, act_0), (1, act_1)]:
            f_act = act.get("farmer") or ["PASS"]
            h_acts = act.get("hands") or []
            for w in [f_act] + h_acts:
                cmd = w[0] if isinstance(w, list) and len(w) > 0 else (w if isinstance(w, str) else "PASS")
                if cmd in ("NORTH", "SOUTH", "EAST", "WEST"): task_counts[p]["MOVE"] += 1
                elif cmd in ("WATER", "WATER_CROP"): task_counts[p]["WATER"] += 1
                elif cmd in ("HARVEST", "HARVEST_CROP"): task_counts[p]["HARVEST"] += 1
                elif cmd in ("TILL", "PLANT"): task_counts[p]["PLANT"] += 1
                elif cmd in ("BUILD_PASTURE", "FEED", "BRUSH", "COLLECT_MILK", "COLLECT_WOOL", "COLLECT_EGG"): task_counts[p]["ANIMAL"] += 1
                elif cmd in ("DROP", "PICKUP"): task_counts[p]["SHED"] += 1
                elif cmd == "PASS": task_counts[p]["PASS"] += 1
                else: task_counts[p]["OTHER"] += 1
                
        q0 = (act_0.get("market") or [])[:10]
        q1 = (act_1.get("market") or [])[:10]
        
        for p, q in [(0, q0), (1, q1)]:
            h_today = 0
            for order in q:
                if isinstance(order, list) and len(order) > 0:
                    op = order[0]
                    if op == "HIRE":
                        hiring_cost[p] += k_env._fib(h_today) * 1
                        h_today += 1
                    elif op == "BUY_LAND":
                        n_q = len(steps[s_idx - 1][p]["observation"]["farms"][p]["unlocked_quadrants"])
                        land_cost[p] += 1000 * n_q
                    elif op == "BUY_SEED":
                        stype = order[1]
                        qty = int(order[2]) if len(order) > 2 else 1
                        scost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(stype, 10) * qty
                        purchases_cost[p]["SEED"] += scost
                    elif op == "BUY_ANIMAL":
                        atype = order[1]
                        qty = int(order[2]) if len(order) > 2 else 1
                        acost = {"COW": 400, "SHEEP": 500, "GOOSE": 200}.get(atype, 400) * qty
                        purchases_cost[p]["ANIMAL"] += acost
                        
        cur_inv = dict(m_inv_start)
        max_q = max(len(q0), len(q1))
        
        sells_step = {0: [], 1: []}
        for idx, order in enumerate(q0):
            if isinstance(order, list) and len(order) > 1 and order[0] == "SELL":
                sells_step[0].append((idx, order[1], int(order[2]) if len(order) > 2 else 1))
        for idx, order in enumerate(q1):
            if isinstance(order, list) and len(order) > 1 and order[0] == "SELL":
                sells_step[1].append((idx, order[1], int(order[2]) if len(order) > 2 else 1))
                
        for slot_c, item_c, qty_c in sells_step[p_cand]:
            for slot_v, item_v, qty_v in sells_step[p_v2]:
                if item_c == item_v:
                    same_step_same_item_collisions += 1
                    if slot_v < slot_c:
                        v2_earlier_slot_collisions += 1
                    elif slot_c < slot_v:
                        cand_earlier_slot_collisions += 1
                    else:
                        same_slot_collisions += 1
                        
        for slot_i in range(max_q):
            ostate_0 = k_env._parse_order(q0[slot_i]) if slot_i < len(q0) else None
            ostate_1 = k_env._parse_order(q1[slot_i]) if slot_i < len(q1) else None
            order_states = [ostate_0, ostate_1]
            
            # Atomic orders (HIRE, BUY_LAND) handled once
            for p in (0, 1):
                if order_states[p] and order_states[p]["type"] in ("HIRE", "BUY_LAND"):
                    order_states[p] = None
            
            while True:
                quoted = [None, None]
                for p in (0, 1):
                    ost = order_states[p]
                    if ost is None or ost.get("remaining", 0) <= 0:
                        continue
                    op = ost["type"]
                    item = ost["item"]
                    if op == "SELL" and item in k_env.PRODUCTS:
                        quoted[p] = ("SELL", item, calc_market_price(item, cur_inv[item]), ost)
                    elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                        quoted[p] = ("BUY_PRODUCT", item, calc_market_price(item, cur_inv[item] - 1), ost)
                    elif op == "BUY_SEED" and item in k_env.CROPS:
                        quoted[p] = ("BUY_SEED", item, k_env.CROPS[item]["seed"], ost)
                    elif op == "BUY_ANIMAL" and item in k_env.ANIMALS:
                        quoted[p] = ("BUY_ANIMAL", item, k_env.ANIMALS[item]["cost"], ost)
                    else:
                        order_states[p] = None
                        
                if all(q is None for q in quoted):
                    break
                    
                for p in (0, 1):
                    if quoted[p] is None:
                        continue
                    op, item, price, ost = quoted[p]
                    if op == "SELL":
                        cur_inv[item] += 1
                        ost["remaining"] -= 1
                        sales_units[p][item] += 1
                        sales_rev_realized[p][item] += price
                        sales_rev_base[p][item] += BASE_PRICES[item]
                        
                        if p == p_cand:
                            cf_rev_cand["realized"] += price
                            cf_rev_cand["base"] += BASE_PRICES[item]
                            
                            v2_sold_this_step_so_far = sum(
                                (qty_v - (order_states[p_v2]["remaining"] if order_states[p_v2] and order_states[p_v2]["item"] == item else 0))
                                for slot_v, item_v, qty_v in sells_step[p_v2] if item_v == item and slot_v <= slot_i
                            )
                            inv_before_v2 = max(0, cur_inv[item] - 1 - max(0, v2_sold_this_step_so_far))
                            p_pre_v2 = calc_market_price(item, inv_before_v2)
                            cf_rev_cand["pre_v2"] += p_pre_v2
                            
                            if slot_i > 0 and any(slot_v < slot_i and item_v == item for slot_v, item_v, _ in sells_step[p_v2]):
                                p_swapped = p_pre_v2
                                cand_priority_loss_dollars += (p_swapped - price)
                                cf_rev_cand["prio_swapped"] += p_swapped
                            else:
                                cf_rev_cand["prio_swapped"] += price
                                
                    elif op == "BUY_PRODUCT":
                        cur_inv[item] -= 1
                        ost["remaining"] -= 1
                        purchases_cost[p][f"PROD_{item}"] += price
                    elif op in ("BUY_SEED", "BUY_ANIMAL"):
                        ost["remaining"] -= 1
                        
    cand_reward = float(steps[-1][p_cand].get("reward") or 0.0)
    v2_reward = float(steps[-1][p_v2].get("reward") or 0.0)
    margin = cand_reward - v2_reward
    
    terminal_unsold_val = {0: 0.0, 1: 0.0}
    final_prices = steps[-1][0]["observation"]["market"]["prices"]
    for p in (0, 1):
        p_priv = steps[-1][p]["observation"].get("private") or {}
        shed = p_priv.get("shed") or {}
        for it, q in shed.items():
            if int(q or 0) > 0 and it in final_prices:
                terminal_unsold_val[p] += int(q) * float(final_prices[it])
        invs = p_priv.get("inventories") or []
        for inv in invs:
            if isinstance(inv, dict):
                for it, q in inv.items():
                    if int(q or 0) > 0 and it in final_prices:
                        terminal_unsold_val[p] += int(q) * float(final_prices[it])
                        
    tot_sales_cand = sum(sales_rev_realized[p_cand].values())
    tot_sales_v2 = sum(sales_rev_realized[p_v2].values())
    tot_costs_cand = sum(purchases_cost[p_cand].values()) + hiring_cost[p_cand] + land_cost[p_cand]
    tot_costs_v2 = sum(purchases_cost[p_v2].values()) + hiring_cost[p_v2] + land_cost[p_v2]
    
    return {
        "seed": seed,
        "cand_seat": cand_seat,
        "cand_reward": cand_reward,
        "v2_reward": v2_reward,
        "margin": margin,
        "win": 1 if cand_reward > v2_reward else (0.5 if cand_reward == v2_reward else 0),
        "tot_sales_cand": tot_sales_cand,
        "tot_sales_v2": tot_sales_v2,
        "tot_costs_cand": tot_costs_cand,
        "tot_costs_v2": tot_costs_v2,
        "sales_units_cand": dict(sales_units[p_cand]),
        "sales_units_v2": dict(sales_units[p_v2]),
        "sales_rev_cand": dict(sales_rev_realized[p_cand]),
        "sales_rev_v2": dict(sales_rev_realized[p_v2]),
        "sales_base_cand": dict(sales_rev_base[p_cand]),
        "sales_base_v2": dict(sales_rev_base[p_v2]),
        "cf_rev_cand": cf_rev_cand,
        "cand_priority_loss_dollars": cand_priority_loss_dollars,
        "collisions": same_step_same_item_collisions,
        "v2_earlier_slot": v2_earlier_slot_collisions,
        "cand_earlier_slot": cand_earlier_slot_collisions,
        "same_slot": same_slot_collisions,
        "unsold_cand": terminal_unsold_val[p_cand],
        "unsold_v2": terminal_unsold_val[p_v2],
        "hiring_cand": hiring_cost[p_cand],
        "hiring_v2": hiring_cost[p_v2],
        "land_cand": land_cost[p_cand],
        "land_v2": land_cost[p_v2],
        "tasks_cand": dict(task_counts[p_cand]),
        "tasks_v2": dict(task_counts[p_v2]),
    }

def run_suite(cand_module_name, seeds, max_workers=10):
    tasks = [(s, cand_module_name, i % 2) for i, s in enumerate(seeds)]
    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_audited_match, s, mod, seat): (s, seat) for s, mod, seat in tasks}
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            if len(results) % 25 == 0 or len(results) == len(seeds):
                print(f"[{cand_module_name}] Completed {len(results)}/{len(seeds)} in {time.time()-t0:.1f}s")
    return results

def decompose_suite_results(results, name):
    n = len(results)
    mean_cand = float(np.mean([r["cand_reward"] for r in results]))
    mean_v2 = float(np.mean([r["v2_reward"] for r in results]))
    mean_margin = float(np.mean([r["margin"] for r in results]))
    win_rate = float(np.mean([r["win"] for r in results]))
    
    mean_sales_c = float(np.mean([r["tot_sales_cand"] for r in results]))
    mean_sales_v = float(np.mean([r["tot_sales_v2"] for r in results]))
    sales_gap = mean_sales_v - mean_sales_c
    
    mean_costs_c = float(np.mean([r["tot_costs_cand"] for r in results]))
    mean_costs_v = float(np.mean([r["tot_costs_v2"] for r in results]))
    costs_gap = mean_costs_c - mean_costs_v
    
    commodities = ["STRAWBERRY", "WOOL", "FERTILIZER", "WHEAT", "MILK", "MELON"]
    unit_gaps = {}
    rev_gaps = {}
    realized_prices_c = {}
    realized_prices_v = {}
    base_rev_gaps = {}
    
    for com in commodities:
        u_c = float(np.mean([r["sales_units_cand"].get(com, 0) for r in results]))
        u_v = float(np.mean([r["sales_units_v2"].get(com, 0) for r in results]))
        r_c = float(np.mean([r["sales_rev_cand"].get(com, 0.0) for r in results]))
        r_v = float(np.mean([r["sales_rev_v2"].get(com, 0.0) for r in results]))
        b_c = float(np.mean([r["sales_base_cand"].get(com, 0.0) for r in results]))
        b_v = float(np.mean([r["sales_base_v2"].get(com, 0.0) for r in results]))
        
        unit_gaps[com] = (u_c, u_v, u_v - u_c)
        rev_gaps[com] = (r_c, r_v, r_v - r_c)
        realized_prices_c[com] = r_c / u_c if u_c > 0 else 0.0
        realized_prices_v[com] = r_v / u_v if u_v > 0 else 0.0
        base_rev_gaps[com] = (b_c, b_v, b_v - b_c)
        
    cf_realized = float(np.mean([r["cf_rev_cand"]["realized"] for r in results]))
    cf_prev2 = float(np.mean([r["cf_rev_cand"]["pre_v2"] for r in results]))
    cf_base = float(np.mean([r["cf_rev_cand"]["base"] for r in results]))
    cf_swapped = float(np.mean([r["cf_rev_cand"]["prio_swapped"] for r in results]))
    prio_loss = float(np.mean([r["cand_priority_loss_dollars"] for r in results]))
    
    total_gap = mean_v2 - mean_cand
    prod_qty_gap = sum(unit_gaps[c][2] * BASE_PRICES[c] for c in commodities)
    order_prio_gap = prio_loss
    market_price_gap = max(0.0, (cf_prev2 - cf_realized) - order_prio_gap)
    
    v2_timing_premium = sum(r_v - b_v for _, (r_c, r_v, _) in rev_gaps.items())
    cl_timing_premium = sum(r_c - b_c for _, (r_c, r_v, _) in rev_gaps.items())
    prod_timing_gap = v2_timing_premium - cl_timing_premium - market_price_gap
    
    costs_c = float(np.mean([r["tot_costs_cand"] for r in results]))
    costs_v = float(np.mean([r["tot_costs_v2"] for r in results]))
    hiring_c = float(np.mean([r["hiring_cand"] for r in results]))
    hiring_v = float(np.mean([r["hiring_v2"] for r in results]))
    land_c = float(np.mean([r["land_cand"] for r in results]))
    land_v = float(np.mean([r["land_v2"] for r in results]))
    
    input_cost_gap = (costs_c - hiring_c - land_c) - (costs_v - hiring_v - land_v)
    labor_cost_gap = hiring_c - hiring_v
    
    move_c = float(np.mean([r["tasks_cand"].get("MOVE", 0) for r in results]))
    move_v = float(np.mean([r["tasks_v2"].get("MOVE", 0) for r in results]))
    extra_move_turns = move_c - move_v
    move_logistics_gap = max(0.0, extra_move_turns * 5.0)
    
    unsold_c = float(np.mean([r["unsold_cand"] for r in results]))
    unsold_v = float(np.mean([r["unsold_v2"] for r in results]))
    terminal_inv_gap = unsold_c - unsold_v
    
    other_gap = total_gap - (prod_qty_gap + prod_timing_gap + input_cost_gap + labor_cost_gap + move_logistics_gap + market_price_gap + order_prio_gap + terminal_inv_gap)
    
    summary = {
        "name": name,
        "n_matches": n,
        "mean_cand_reward": mean_cand,
        "mean_v2_reward": mean_v2,
        "mean_margin": mean_margin,
        "total_gap": total_gap,
        "win_rate": win_rate,
        "tot_sales_cand": mean_sales_c,
        "tot_sales_v2": mean_sales_v,
        "tot_costs_cand": mean_costs_c,
        "tot_costs_v2": mean_costs_v,
        "unit_gaps": {k: {"cand": v[0], "v2": v[1], "delta": v[2]} for k, v in unit_gaps.items()},
        "rev_gaps": {k: {"cand": v[0], "v2": v[1], "delta": v[2]} for k, v in rev_gaps.items()},
        "realized_prices_c": realized_prices_c,
        "realized_prices_v": realized_prices_v,
        "counterfactuals": {
            "A_realized_cand_rev": cf_realized,
            "B_pre_v2_cand_rev": cf_prev2,
            "C_base_cand_rev": cf_base,
            "D_prio_swapped_cand_rev": cf_swapped,
            "market_order_priority_loss": prio_loss,
            "macro_market_suppression_loss": cf_prev2 - cf_realized
        },
        "nine_component_decomposition": {
            "1_production_quantity_gap": prod_qty_gap,
            "2_production_timing_gap": prod_timing_gap,
            "3_input_cost_gap": input_cost_gap,
            "4_labor_cost_gap": labor_cost_gap,
            "5_movement_logistics_gap": move_logistics_gap,
            "6_market_price_gap": market_price_gap,
            "7_order_priority_gap": order_prio_gap,
            "8_terminal_inventory_gap": terminal_inv_gap,
            "9_other_residual": other_gap
        },
        "collisions_summary": {
            "same_step_same_item": float(np.mean([r["collisions"] for r in results])),
            "v2_earlier_slot": float(np.mean([r["v2_earlier_slot"] for r in results])),
            "cand_earlier_slot": float(np.mean([r["cand_earlier_slot"] for r in results])),
            "same_slot": float(np.mean([r["same_slot"] for r in results]))
        }
    }
    return summary

if __name__ == "__main__":
    seeds = list(range(5000, 5100))
    
    print("=" * 80)
    print("RECONCILING H2H ACCOUNTING DISCREPANCY ACROSS 100 MATCHED SEEDS (5000-5099)")
    print("=" * 80)
    
    print("\n--- 1. AUDITING FROZEN V2 VS CL-ECONOMIC-V1 ---")
    res_econ = run_suite("candidates.candidate_cl_economic_v1", seeds)
    summary_econ = decompose_suite_results(res_econ, "CL-Economic-V1")
    
    print("\n--- 2. AUDITING FROZEN V2 VS CL-TEMPORAL-V3 ---")
    res_temp3 = run_suite("candidates.candidate_cl_temporal_v3", seeds)
    summary_temp3 = decompose_suite_results(res_temp3, "CL-Temporal-V3")
    
    print("\n--- 3. AUDITING FROZEN V2 VS CL-TEMPORAL-V2 (Investigating -$63.5k Claim) ---")
    res_temp2 = run_suite("candidates.candidate_cl_temporal_v2", seeds)
    summary_temp2 = decompose_suite_results(res_temp2, "CL-Temporal-V2")
    
    full_forensic_report = {
        "cl_economic_v1": summary_econ,
        "cl_temporal_v3": summary_temp3,
        "cl_temporal_v2": summary_temp2
    }
    
    with open("scratch/h2h_reconciliation_accounting_results.json", "w") as f:
        json.dump(full_forensic_report, f, indent=2)
        
    print("\nSaved full reconciliation report to scratch/h2h_reconciliation_accounting_results.json")
