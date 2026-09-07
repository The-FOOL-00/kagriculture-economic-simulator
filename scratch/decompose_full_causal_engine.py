import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
import kaggle_environments
import numpy as np

from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def instrument_episode(agent_fn, seed, opp_type="starter"):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    opp_fn = kaggle_environments.environments['kaggriculture']['agents'][opp_type]
    env.run([agent_fn, opp_fn])
    
    financials = {
        "crop_revenue": {"MELON": 0.0, "STRAWBERRY": 0.0, "WHEAT": 0.0, "TOMATO": 0.0, "CARROT": 0.0},
        "livestock_revenue": {"MILK": 0.0, "WOOL": 0.0, "EGG": 0.0, "FERTILIZER": 0.0},
        "costs": {"SEEDS": 0.0, "ANIMALS": 0.0, "FEED": 0.0, "LAND": 0.0, "HIRES": 0.0},
        "units_sold": {"MELON": 0, "STRAWBERRY": 0, "WHEAT": 0, "TOMATO": 0, "CARROT": 0, "MILK": 0, "WOOL": 0, "EGG": 0, "FERTILIZER": 0},
    }
    
    actions_breakdown = {
        "WATER": 0, "HARVEST": 0, "PLANT": 0, "FEED": 0, "CARE": 0,
        "COLLECT_FERTILIZER": 0, "FERTILIZE": 0, "BUILD_PASTURE": 0,
        "PLACE": 0, "PICKUP": 0, "DIG": 0, "MOVE": 0, "PASS": 0, "FAILED": 0
    }
    
    cash_trajectory = []
    
    # Audit steps
    for s_idx in range(1, len(env.steps)):
        s_prev = env.steps[s_idx-1][0]['observation']
        s_cur = env.steps[s_idx][0]['observation']
        act0 = env.steps[s_idx][0]['action']
        
        f_cur = s_cur['farms'][0]
        f_prev = s_prev['farms'][0]
        m0_post = f_cur['money']
        
        if (s_idx - 1) % 24 == 0 or s_idx == len(env.steps) - 1:
            cash_trajectory.append(m0_post)
            
        m_act = act0.get('market', []) if isinstance(act0, dict) else []
        prices = (s_prev.get('market') or {}).get('prices') or {}
        shed_prev = (s_prev.get('private') or {}).get('shed') or {}
        
        # Sells
        for order in m_act:
            if isinstance(order, list) and len(order) >= 3 and order[0] == 'SELL':
                item, qty = order[1], int(order[2])
                p = float(prices.get(item, 0) or 0)
                avail = int(shed_prev.get(item, 0) or 0)
                sold_qty = min(qty, avail)
                if sold_qty > 0:
                    revenue = sold_qty * p
                    financials["units_sold"][item] = financials["units_sold"].get(item, 0) + sold_qty
                    if item in financials["crop_revenue"]:
                        financials["crop_revenue"][item] += revenue
                    elif item in financials["livestock_revenue"]:
                        financials["livestock_revenue"][item] += revenue
            elif isinstance(order, list) and order[0] == 'BUY_PRODUCT' and len(order) >= 3:
                item, qty = order[1], int(order[2])
                p = float(prices.get(item, 30) or 30)
                financials["costs"]["FEED"] += qty * p
            elif isinstance(order, list) and order[0] == 'BUY_SEED' and len(order) >= 3:
                crop, qty = order[1], int(order[2])
                sp = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(crop, 50)
                financials["costs"]["SEEDS"] += qty * sp
            elif isinstance(order, list) and order[0] == 'BUY_ANIMAL' and len(order) >= 3:
                an, qty = order[1], int(order[2])
                ap = {"COW": 400, "SHEEP": 500, "GOOSE": 250}.get(an, 400)
                financials["costs"]["ANIMALS"] += qty * ap
            elif isinstance(order, list) and order[0] == 'BUY_LAND':
                financials["costs"]["LAND"] += 1000
                
        # Action counts
        all_units = [act0.get('farmer', ['PASS'])] + (act0.get('hands', []) if isinstance(act0, dict) else [])
        for u in all_units:
            if not u:
                actions_breakdown["PASS"] += 1
                continue
            op = u[0] if isinstance(u, (list, tuple)) else str(u)
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                actions_breakdown["MOVE"] += 1
            elif op in actions_breakdown:
                actions_breakdown[op] += 1
            else:
                actions_breakdown["FAILED"] += 1

    final_reward = env.steps[-1][0]['reward']
    return {
        "final_reward": final_reward,
        "financials": financials,
        "actions": actions_breakdown,
        "cash_trajectory": cash_trajectory
    }

def run_study():
    seeds = [42, 100, 2024, 104816794, 104817623]
    v2_runs = []
    prime_runs = []
    
    print(f"Running Phase 1 Full Decomposition across {len(seeds)} seeds...")
    for sd in seeds:
        print(f"  Profiling Seed {sd}...")
        v2_res = instrument_episode(v2_agent, sd)
        prime_res = instrument_episode(prime_agent, sd)
        v2_runs.append(v2_res)
        prime_runs.append(prime_res)
        
    v2_mean_reward = float(np.mean([r['final_reward'] for r in v2_runs]))
    prime_mean_reward = float(np.mean([r['final_reward'] for r in prime_runs]))
    gap = v2_mean_reward - prime_mean_reward
    
    print("\n" + "="*80)
    print("PHASE 1: RECONCILING THE REWARD CONTRADICTION")
    print("="*80)
    print(f"V2 Mean Reward:    ${v2_mean_reward:,.2f}")
    print(f"Prime Mean Reward: ${prime_mean_reward:,.2f}")
    print(f"Performance Gap:   ${gap:,.2f}")
    print("="*80)
    
    crops = ["MELON", "STRAWBERRY", "WHEAT", "TOMATO", "CARROT"]
    print("\n--- CROP REVENUE COMPARISON (MEAN $) ---")
    crop_gap_total = 0.0
    for c in crops:
        v2_c = float(np.mean([r['financials']['crop_revenue'][c] for r in v2_runs]))
        p_c = float(np.mean([r['financials']['crop_revenue'][c] for r in prime_runs]))
        diff = v2_c - p_c
        crop_gap_total += diff
        pct = (diff / gap) * 100 if gap != 0 else 0
        v2_sold = float(np.mean([r['financials']['units_sold'][c] for r in v2_runs]))
        p_sold = float(np.mean([r['financials']['units_sold'][c] for r in prime_runs]))
        print(f"  {c:<12}: V2=${v2_c:>10,.1f} ({v2_sold:>5.1f} sold) | Prime=${p_c:>10,.1f} ({p_sold:>5.1f} sold) | Delta=${diff:>10,.1f} ({pct:>5.1f}%)")
        
    livestock = ["MILK", "WOOL", "EGG", "FERTILIZER"]
    print("\n--- LIVESTOCK REVENUE COMPARISON (MEAN $) ---")
    live_gap_total = 0.0
    for l in livestock:
        v2_l = float(np.mean([r['financials']['livestock_revenue'][l] for r in v2_runs]))
        p_l = float(np.mean([r['financials']['livestock_revenue'][l] for r in prime_runs]))
        diff = v2_l - p_l
        live_gap_total += diff
        pct = (diff / gap) * 100 if gap != 0 else 0
        v2_sold = float(np.mean([r['financials']['units_sold'][l] for r in v2_runs]))
        p_sold = float(np.mean([r['financials']['units_sold'][l] for r in prime_runs]))
        print(f"  {l:<12}: V2=${v2_l:>10,.1f} ({v2_sold:>5.1f} sold) | Prime=${p_l:>10,.1f} ({p_sold:>5.1f} sold) | Delta=${diff:>10,.1f} ({pct:>5.1f}%)")
        
    print("\n--- ACTION ACCOUNTING COMPARISON (MEAN ACTION COUNTS) ---")
    for act_name in ["WATER", "HARVEST", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER", "BUILD_PASTURE", "MOVE", "PASS"]:
        v2_a = float(np.mean([r['actions'][act_name] for r in v2_runs]))
        p_a = float(np.mean([r['actions'][act_name] for r in prime_runs]))
        diff = v2_a - p_a
        print(f"  {act_name:<18}: V2={v2_a:>7.1f} | Prime={p_a:>7.1f} | Delta={diff:>+7.1f}")
        
    print("\n--- CUMULATIVE CASH TRAJECTORY (DAILY) ---")
    days = [0, 4, 9, 10, 14, 19, 24, 29]
    for d in days:
        step_idx = min(d, len(v2_runs[0]['cash_trajectory'])-1)
        v2_cash = float(np.mean([r['cash_trajectory'][step_idx] for r in v2_runs]))
        p_cash = float(np.mean([r['cash_trajectory'][step_idx] for r in prime_runs]))
        print(f"  Day {d:>2}: V2=${v2_cash:>10,.1f} | Prime=${p_cash:>10,.1f} | Delta=${v2_cash - p_cash:>10,.1f}")

    summary = {
        "v2_mean_reward": v2_mean_reward,
        "prime_mean_reward": prime_mean_reward,
        "gap": gap,
        "crop_gap_total": crop_gap_total,
        "live_gap_total": live_gap_total,
        "crop_gap_pct": (crop_gap_total / gap) * 100,
        "live_gap_pct": (live_gap_total / gap) * 100
    }
    with open("scratch/phase1_decomposition_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved summary to scratch/phase1_decomposition_summary.json")

if __name__ == "__main__":
    run_study()
