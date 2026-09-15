"""
Run Full 100-Seed Head-to-Head Forensic Audit: Frozen V2 vs CL-Economic-V1
Seeds: 5000-5099 (100 matches, alternating seats).
Computes exact aggregated wealth decomposition, commodity volume & pricing,
strawberry yield breakdown, market priority resolution, and task allocations.
"""

import sys
import os
import json
import time
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scratch.deep_h2h_market_and_yield_auditor import run_forensic_suite

SEEDS = list(range(5000, 5100))

def summarize_h2h_results(results):
    n = len(results)
    cl_rewards = np.array([r["cl_reward"] for r in results])
    v2_rewards = np.array([r["v2_reward"] for r in results])
    margins = np.array([r["margin"] for r in results])
    
    boot_means = [np.mean(np.random.choice(margins, size=n, replace=True)) for _ in range(5000)]
    ci_lower, ci_upper = np.percentile(boot_means, [2.5, 97.5])
    
    # Aggregated Sales & Prices
    commodities = ["STRAWBERRY", "MELON", "MILK", "WOOL", "FERTILIZER", "WHEAT", "EGG"]
    sales_summary = {}
    for c in commodities:
        cl_u = [r["cl_sales"].get(c, {}).get("units", 0) for r in results]
        cl_r = [r["cl_sales"].get(c, {}).get("rev", 0.0) for r in results]
        v2_u = [r["v2_sales"].get(c, {}).get("units", 0) for r in results]
        v2_r = [r["v2_sales"].get(c, {}).get("rev", 0.0) for r in results]
        
        cl_mean_u = float(np.mean(cl_u))
        cl_mean_r = float(np.mean(cl_r))
        cl_avg_p = cl_mean_r / cl_mean_u if cl_mean_u > 0 else 0.0
        
        v2_mean_u = float(np.mean(v2_u))
        v2_mean_r = float(np.mean(v2_r))
        v2_avg_p = v2_mean_r / v2_mean_u if v2_mean_u > 0 else 0.0
        
        sales_summary[c] = {
            "cl_units": cl_mean_u, "cl_rev": cl_mean_r, "cl_avg_price": cl_avg_p,
            "v2_units": v2_mean_u, "v2_rev": v2_mean_r, "v2_avg_price": v2_avg_p,
            "rev_delta_v2_minus_cl": v2_mean_r - cl_mean_r
        }
        
    # Aggregated Harvests
    harvest_summary = {}
    for c in ["STRAWBERRY", "MELON", "WHEAT"]:
        cl_y = [r["cl_harvests"].get(c, {}).get("total_yield", 0) for r in results]
        v2_y = [r["v2_harvests"].get(c, {}).get("total_yield", 0) for r in results]
        cl_ev = [r["cl_harvests"].get(c, {}).get("harvest_events", 0) for r in results]
        v2_ev = [r["v2_harvests"].get(c, {}).get("harvest_events", 0) for r in results]
        cl_1 = [r["cl_harvests"].get(c, {}).get("yield_1_count", 0) for r in results]
        v2_1 = [r["v2_harvests"].get(c, {}).get("yield_1_count", 0) for r in results]
        cl_2p = [r["cl_harvests"].get(c, {}).get("yield_2plus_count", 0) for r in results]
        v2_2p = [r["v2_harvests"].get(c, {}).get("yield_2plus_count", 0) for r in results]
        
        harvest_summary[c] = {
            "cl_total_yield": float(np.mean(cl_y)),
            "cl_harvest_events": float(np.mean(cl_ev)),
            "cl_yield_1_pct": float(np.mean(cl_1)) / float(np.mean(cl_ev)) * 100.0 if np.mean(cl_ev) > 0 else 0.0,
            "cl_yield_2plus_count": float(np.mean(cl_2p)),
            "v2_total_yield": float(np.mean(v2_y)),
            "v2_harvest_events": float(np.mean(v2_ev)),
            "v2_yield_1_pct": float(np.mean(v2_1)) / float(np.mean(v2_ev)) * 100.0 if np.mean(v2_ev) > 0 else 0.0,
            "v2_yield_2plus_count": float(np.mean(v2_2p)),
        }

    # Purchases & Capital Expenditures
    purch_summary = {}
    all_purch = ["COW", "SHEEP", "FEED", "SEED_MELON", "SEED_STRAWBERRY", "SEED_WHEAT", "BUY_LAND", "HIRE"]
    for p_item in all_purch:
        key = "WHEAT" if p_item == "FEED" else p_item
        cl_cost = [r["cl_purchases"].get(key, {}).get("cost", 0.0) for r in results]
        v2_cost = [r["v2_purchases"].get(key, {}).get("cost", 0.0) for r in results]
        cl_units = [r["cl_purchases"].get(key, {}).get("units", 0) for r in results]
        v2_units = [r["v2_purchases"].get(key, {}).get("units", 0) for r in results]
        purch_summary[p_item] = {
            "cl_units": float(np.mean(cl_units)),
            "cl_cost": float(np.mean(cl_cost)),
            "v2_units": float(np.mean(v2_units)),
            "v2_cost": float(np.mean(v2_cost)),
        }

    # Unsold Inventory
    cl_unsold_val = float(np.mean([r["cl_unsold_val"] for r in results]))
    v2_unsold_val = float(np.mean([r["v2_unsold_val"] for r in results]))
    
    # Front-running collisions
    collision_summary = {}
    for it in ["STRAWBERRY", "MELON", "MILK", "WOOL", "FERTILIZER", "WHEAT"]:
        colls = [r["front_run_stats"].get(it, {}).get("collision_events", 0) for r in results]
        v2_first = [r["front_run_stats"].get(it, {}).get("v2_first_count", 0) for r in results]
        cl_first = [r["front_run_stats"].get(it, {}).get("cl_first_count", 0) for r in results]
        collision_summary[it] = {
            "mean_collisions": float(np.mean(colls)),
            "v2_first_pct": float(np.mean(v2_first)) / float(np.mean(colls)) * 100.0 if np.mean(colls) > 0 else 0.0,
            "cl_first_pct": float(np.mean(cl_first)) / float(np.mean(colls)) * 100.0 if np.mean(colls) > 0 else 0.0
        }
        
    # Tasks
    task_keys = ["MOVEMENT", "WATER", "HARVEST", "PLANT", "LIVESTOCK", "SHED", "PASS"]
    task_summary = {}
    for tk in task_keys:
        cl_t = [r["cl_tasks"].get(tk, 0) for r in results]
        v2_t = [r["v2_tasks"].get(tk, 0) for r in results]
        task_summary[tk] = {
            "cl_turns": float(np.mean(cl_t)),
            "v2_turns": float(np.mean(v2_t)),
            "delta": float(np.mean(cl_t)) - float(np.mean(v2_t))
        }

    summary = {
        "n_matches": n,
        "cl_mean_reward": float(np.mean(cl_rewards)),
        "cl_std_reward": float(np.std(cl_rewards)),
        "cl_median_reward": float(np.median(cl_rewards)),
        "v2_mean_reward": float(np.mean(v2_rewards)),
        "v2_std_reward": float(np.std(v2_rewards)),
        "v2_median_reward": float(np.median(v2_rewards)),
        "mean_net_margin": float(np.mean(margins)),
        "median_net_margin": float(np.median(margins)),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "sales_summary": sales_summary,
        "harvest_summary": harvest_summary,
        "purch_summary": purch_summary,
        "cl_unsold_val": cl_unsold_val,
        "v2_unsold_val": v2_unsold_val,
        "collision_summary": collision_summary,
        "task_summary": task_summary
    }
    
    return summary

def main():
    print("=" * 80)
    print("PHASE 1: 100-MATCH HEAD-TO-HEAD FORENSIC AUDIT (Seeds 5000-5099)")
    print("=" * 80)
    
    raw_results = run_forensic_suite(SEEDS, max_workers=10)
    summary = summarize_h2h_results(raw_results)
    
    output_path = os.path.join(PROJECT_ROOT, "scratch", "h2h_forensic_100seeds_results.json")
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "raw_sample": raw_results[:5]}, f, indent=2)
    print(f"\nSaved detailed results to {output_path}")
    
    # Print formatted tables
    print("\n" + "=" * 90)
    print("EXACT HEAD-TO-HEAD REWARD & MARGIN SUMMARY (N = 100 Matches, Alternating Seats)")
    print("=" * 90)
    print(f"CL-Economic-V1 Mean Reward: ${summary['cl_mean_reward']:12,.2f} ± ${summary['cl_std_reward']:10,.2f} (Median: ${summary['cl_median_reward']:10,.2f})")
    print(f"Frozen V2 Mean Reward:       ${summary['v2_mean_reward']:12,.2f} ± ${summary['v2_std_reward']:10,.2f} (Median: ${summary['v2_median_reward']:10,.2f})")
    print(f"Mean Net Margin (CL - V2):   ${summary['mean_net_margin']:12,.2f} [95% CI: ${summary['ci_95_lower']:,.2f}, ${summary['ci_95_upper']:,.2f}]")
    print("-" * 90)
    
    print("\n--- COMMODITY SALES, REVENUE & REALIZED PRICES ---")
    print(f"{'COMMODITY':<12} | {'V2 UNITS':<8} | {'V2 REV':<10} | {'V2 PRICE':<8} | {'CL UNITS':<8} | {'CL REV':<10} | {'CL PRICE':<8} | {'REV DELTA':<12}")
    print("-" * 90)
    tot_v2_rev = sum(v["v2_rev"] for v in summary["sales_summary"].values())
    tot_cl_rev = sum(v["cl_rev"] for v in summary["sales_summary"].values())
    for it, d in summary["sales_summary"].items():
        print(f"{it:<12} | {d['v2_units']:8.1f} | ${d['v2_rev']:9,.1f} | ${d['v2_avg_price']:7.1f} | {d['cl_units']:8.1f} | ${d['cl_rev']:9,.1f} | ${d['cl_avg_price']:7.1f} | +${d['rev_delta_v2_minus_cl']:10,.1f}")
    print("-" * 90)
    print(f"{'TOTAL SALES':<12} | {'-':<8} | ${tot_v2_rev:9,.1f} | {'-':<8} | {'-':<8} | ${tot_cl_rev:9,.1f} | {'-':<8} | +${tot_v2_rev - tot_cl_rev:10,.1f}")
    
    print("\n--- HARVEST & YIELD ANALYSIS ---")
    for c, hd in summary["harvest_summary"].items():
        print(f"{c:<12} | V2: Yield {hd['v2_total_yield']:5.1f} in {hd['v2_harvest_events']:4.1f} harvests (1-unit: {hd['v2_yield_1_pct']:4.1f}%, 2+unit: {hd['v2_yield_2plus_count']:4.1f})")
        print(f"{'':<12} | CL: Yield {hd['cl_total_yield']:5.1f} in {hd['cl_harvest_events']:4.1f} harvests (1-unit: {hd['cl_yield_1_pct']:4.1f}%, 2+unit: {hd['cl_yield_2plus_count']:4.1f})")
        
    print("\n--- FRONT-RUNNING & MARKET SLOT COLLISIONS ---")
    print(f"{'PRODUCT':<12} | {'COLLISIONS':<11} | {'V2 FIRST %':<11} | {'CL FIRST %':<11}")
    print("-" * 60)
    for it, cd in summary["collision_summary"].items():
        print(f"{it:<12} | {cd['mean_collisions']:11.1f} | {cd['v2_first_pct']:10.1f}% | {cd['cl_first_pct']:10.1f}%")
        
    print("\n--- TERMINAL ASSETS & UNSOLD VALUE ---")
    print(f"CL Unsold Terminal Inventory Value: ${summary['cl_unsold_val']:10,.2f}")
    print(f"V2 Unsold Terminal Inventory Value: ${summary['v2_unsold_val']:10,.2f}")
    print(f"Net Unsold Advantage (CL - V2):    ${summary['cl_unsold_val'] - summary['v2_unsold_val']:10,.2f}")
    
    print("\n--- TASK ALLOCATION (TURNS SPENT) ---")
    for tk, td in summary["task_summary"].items():
        print(f"{tk:<12} | V2: {td['v2_turns']:6.1f} | CL: {td['cl_turns']:6.1f} | Delta (CL - V2): {td['delta']:+6.1f}")
    print("=" * 90)

if __name__ == "__main__":
    main()
