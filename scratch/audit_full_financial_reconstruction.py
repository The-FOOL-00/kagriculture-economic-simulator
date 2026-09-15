import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.candidate_cl_pair_m1_m3 import agent as cl_m1_m3

SEEDS = list(range(1000, 1010))

def run_and_extract_telemetry(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])

    # Physical harvests
    harvests = {"STRAWBERRY": 0, "WOOL": 0, "WHEAT": 0, "MELON": 0, "MILK": 0, "EGG": 0}
    # Fertilizer accounting
    fert_collected = 0
    fert_applied = 0
    fert_sold = 0
    
    # Sales tracking by commodity
    sales_qty = {k: 0 for k in harvests}
    sales_qty["FERTILIZER"] = 0
    sales_rev = {k: 0.0 for k in sales_qty}
    
    # Strawberry price tracking
    straw_prices_seen = []
    straw_sale_prices = []
    
    # Daily cash, shed, pockets
    daily_cash = []
    daily_shed = []
    daily_straw_prices = []

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        day = prev_obs["day"]
        hour = prev_obs["hour"]
        prev_farm = prev_obs["farms"][0]
        prev_tiles = prev_farm["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        prev_farmer = prev_farm["farmer"]
        prev_hands = prev_farm["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]
        prices = prev_obs["market"]["prices"]

        if "STRAWBERRY" in prices:
            straw_prices_seen.append(prices["STRAWBERRY"])

        # Market sales in act
        for m in act.get("market", []):
            if len(m) >= 3 and m[0] == "SELL":
                item = m[1]
                qty = int(m[2])
                pr = prices.get(item, 0)
                if item in sales_qty:
                    sales_qty[item] += qty
                    sales_rev[item] += qty * pr
                if item == "STRAWBERRY":
                    straw_sale_prices.append(pr)
                if item == "FERTILIZER":
                    fert_sold += qty

        # Worker actions
        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or len(w_act) == 0: continue
            if w_idx >= len(prev_workers) or prev_workers[w_idx] is None: continue
            wx, wy = prev_workers[w_idx]
            pt = prev_tiles[wy][wx]
            op = w_act[0]

            if op == "COLLECT_FERTILIZER":
                fert_collected += 1
            elif op == "FERTILIZE":
                fert_applied += 1
            elif op == "HARVEST" and isinstance(pt, dict):
                crop = pt.get("crop")
                animal = pt.get("animal")
                yu = pt.get("yield_units", 0)
                if crop in harvests:
                    harvests[crop] += yu
                elif animal == "COW":
                    harvests["MILK"] += yu
                elif animal == "SHEEP":
                    harvests["WOOL"] += yu

        if hour == 23:
            daily_cash.append(curr_obs["farms"][0]["money"])
            daily_shed.append(dict(curr_obs["private"]["shed"]))
            daily_straw_prices.append(prices.get("STRAWBERRY", 0))

    final_obs = steps[-1][0]["observation"]
    reward = final_obs["farms"][0]["money"]
    final_shed_fert = final_obs["private"]["shed"].get("FERTILIZER", 0)
    final_pocket_fert = sum(inv.get("FERTILIZER", 0) for inv in final_obs["private"]["inventories"])

    return {
        "reward": reward,
        "harvests": harvests,
        "fert_collected": fert_collected,
        "fert_applied": fert_applied,
        "fert_sold": fert_sold,
        "fert_remaining": final_shed_fert + final_pocket_fert,
        "sales_qty": sales_qty,
        "sales_rev": sales_rev,
        "straw_avg_sale_price": float(np.mean(straw_sale_prices)) if straw_sale_prices else 0.0,
        "straw_min_price": min(straw_prices_seen) if straw_prices_seen else 0,
        "straw_max_price": max(straw_prices_seen) if straw_prices_seen else 0,
        "straw_sale_prices": straw_sale_prices,
        "daily_cash": daily_cash,
        "daily_shed": daily_shed,
        "daily_straw_prices": daily_straw_prices
    }

def main():
    print("="*90)
    print("PHASE 2 & 3: FULL FINANCIAL & PRODUCTION RECONSTRUCTION (SEEDS 1000-1009)")
    print("="*90)

    results = {"Baseline": [], "Gated": [], "M1_M3": []}

    for seed in SEEDS:
        print(f"Running Seed {seed} across Baseline, Gated (M1), and M1+M3...")
        b = run_and_extract_telemetry(cl_baseline, seed)
        g = run_and_extract_telemetry(cl_gated, seed)
        m = run_and_extract_telemetry(cl_m1_m3, seed)
        results["Baseline"].append(b)
        results["Gated"].append(g)
        results["M1_M3"].append(m)

    # Compute comparison metrics
    b_rew = [r["reward"] for r in results["Baseline"]]
    g_rew = [r["reward"] for r in results["Gated"]]
    m_rew = [r["reward"] for r in results["M1_M3"]]

    b_straw = [r["harvests"]["STRAWBERRY"] for r in results["Baseline"]]
    g_straw = [r["harvests"]["STRAWBERRY"] for r in results["Gated"]]
    m_straw = [r["harvests"]["STRAWBERRY"] for r in results["M1_M3"]]

    d_straw_m1 = np.array(g_straw) - np.array(b_straw)
    d_straw_m1m3 = np.array(m_straw) - np.array(b_straw)
    d_rew_m1 = np.array(g_rew) - np.array(b_rew)
    d_rew_m1m3 = np.array(m_rew) - np.array(b_rew)

    print("\n" + "="*90)
    print(f"{'Metric':<32} | {'Baseline (CL)':<15} | {'Gated (M1)':<15} | {'Delta (M1 - Base)':<18}")
    print("-" * 86)
    print(f"{'Terminal Reward ($)':<32} | ${np.mean(b_rew):<14,.1f} | ${np.mean(g_rew):<14,.1f} | {np.mean(d_rew_m1):<+18,.1f}")
    print(f"{'Strawberry Harvest (units)':<32} | {np.mean(b_straw):<15.2f} | {np.mean(g_straw):<15.2f} | {np.mean(d_straw_m1):<+18.2f}")
    print(f"{'Strawberry Sales Qty (units)':<32} | {np.mean([r['sales_qty']['STRAWBERRY'] for r in results['Baseline']]):<15.2f} | {np.mean([r['sales_qty']['STRAWBERRY'] for r in results['Gated']]):<15.2f} | {np.mean([r['sales_qty']['STRAWBERRY'] for r in results['Gated']]) - np.mean([r['sales_qty']['STRAWBERRY'] for r in results['Baseline']]):<+18.2f}")
    print(f"{'Strawberry Sales Revenue ($)':<32} | ${np.mean([r['sales_rev']['STRAWBERRY'] for r in results['Baseline']]):<14,.1f} | ${np.mean([r['sales_rev']['STRAWBERRY'] for r in results['Gated']]):<14,.1f} | {np.mean([r['sales_rev']['STRAWBERRY'] for r in results['Gated']]) - np.mean([r['sales_rev']['STRAWBERRY'] for r in results['Baseline']]):<+18,.1f}")
    print(f"{'Strawberry Avg Sale Price ($)':<32} | ${np.mean([r['straw_avg_sale_price'] for r in results['Baseline']]):<14.1f} | ${np.mean([r['straw_avg_sale_price'] for r in results['Gated']]):<14.1f} | {np.mean([r['straw_avg_sale_price'] for r in results['Gated']]) - np.mean([r['straw_avg_sale_price'] for r in results['Baseline']]):<+18.1f}")
    print(f"{'Fertilizer Collected (actions)':<32} | {np.mean([r['fert_collected'] for r in results['Baseline']]):<15.2f} | {np.mean([r['fert_collected'] for r in results['Gated']]):<15.2f} | {np.mean([r['fert_collected'] for r in results['Gated']]) - np.mean([r['fert_collected'] for r in results['Baseline']]):<+18.2f}")
    print(f"{'Fertilizer Applied (actions)':<32} | {np.mean([r['fert_applied'] for r in results['Baseline']]):<15.2f} | {np.mean([r['fert_applied'] for r in results['Gated']]):<15.2f} | {np.mean([r['fert_applied'] for r in results['Gated']]) - np.mean([r['fert_applied'] for r in results['Baseline']]):<+18.2f}")
    print(f"{'Fertilizer Sold (units)':<32} | {np.mean([r['fert_sold'] for r in results['Baseline']]):<15.2f} | {np.mean([r['fert_sold'] for r in results['Gated']]):<15.2f} | {np.mean([r['fert_sold'] for r in results['Gated']]) - np.mean([r['fert_sold'] for r in results['Baseline']]):<+18.2f}")
    print(f"{'Fertilizer Remaining in Farm':<32} | {np.mean([r['fert_remaining'] for r in results['Baseline']]):<15.2f} | {np.mean([r['fert_remaining'] for r in results['Gated']]):<15.2f} | {np.mean([r['fert_remaining'] for r in results['Gated']]) - np.mean([r['fert_remaining'] for r in results['Baseline']]):<+18.2f}")
    print("="*90)

    print("\nM1+M3 (Fertilizer Gating + Immediate Harvest) Comparison:")
    print(f"Strawberry Harvest Mean: {np.mean(m_straw):.2f} (Delta vs Base: {np.mean(d_straw_m1m3):+.2f} units)")
    print(f"Terminal Reward Mean:   ${np.mean(m_rew):,.1f} (Delta vs Base: {np.mean(d_rew_m1m3):+,.1f})")

    print("\nStatistical Rigor of Strawberry Gains:")
    print(f"M1 Strawberry Delta:   Mean = {np.mean(d_straw_m1):+.2f}, Median = {np.median(d_straw_m1):+.1f}, Min = {np.min(d_straw_m1):+d}, Max = {np.max(d_straw_m1):+d}, Std = {np.std(d_straw_m1):.2f}")
    print(f"M1+M3 Strawberry Delta: Mean = {np.mean(d_straw_m1m3):+.2f}, Median = {np.median(d_straw_m1m3):+.1f}, Min = {np.min(d_straw_m1m3):+d}, Max = {np.max(d_straw_m1m3):+d}, Std = {np.std(d_straw_m1m3):.2f}")

    print("\nPer-Seed Breakdown for Strawberry Harvest & Terminal Reward:")
    print(f"{'Seed':<6} | {'Base Rew':<10} | {'Gated Rew':<10} | {'Delta Rew':<10} | {'Base Str':<9} | {'Gated Str':<10} | {'Delta Str':<10} | {'M1+M3 Str':<10} | {'Delta M1M3':<10}")
    print("-" * 95)
    for i, s in enumerate(SEEDS):
        print(f"{s:<6} | ${int(b_rew[i]):<9,d} | ${int(g_rew[i]):<9,d} | ${int(d_rew_m1[i]):<+9,d} | {b_straw[i]:<9} | {g_straw[i]:<10} | {d_straw_m1[i]:<+10} | {m_straw[i]:<10} | {d_straw_m1m3[i]:<+10}")
    print("="*95)

    os.makedirs("scratch", exist_ok=True)
    with open("scratch/full_financial_reconstruction.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
