import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import numpy as np

from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def run_exact_accounting(agent_fn, agent_name, seed=42, opp_name="starter"):
    # Data collectors
    sales_by_item = {}      # item -> {"units": 0, "revenue": 0.0}
    purchases_by_item = {}  # item -> {"units": 0, "cost": 0.0}
    hires_cost = 0.0
    hires_count = 0
    land_cost = 0.0
    land_count = 0
    
    orig_process_market = kg._process_market
    
    def hooked_process_market(state, env_inner):
        # We wrap _commit_unit, _do_hire, _do_buy_land during market processing
        orig_commit = kg._commit_unit
        orig_hire = kg._do_hire
        orig_buy_land = kg._do_buy_land
        
        farm0 = state[0].observation.farms[0]
        
        def hooked_commit(op, item, price, farm, private, market, shed_capacity=100):
            res = orig_commit(op, item, price, farm, private, market, shed_capacity)
            if res and farm is farm0:
                if op == "SELL":
                    if item not in sales_by_item:
                        sales_by_item[item] = {"units": 0, "revenue": 0.0}
                    sales_by_item[item]["units"] += 1
                    sales_by_item[item]["revenue"] += price
                elif op.startswith("BUY_"):
                    key = f"{op}_{item}"
                    if key not in purchases_by_item:
                        purchases_by_item[key] = {"units": 0, "cost": 0.0}
                    purchases_by_item[key]["units"] += 1
                    purchases_by_item[key]["cost"] += price
            return res
            
        def hooked_hire(farm, private, board_size, hire_mult):
            nonlocal hires_cost, hires_count
            m_pre = farm["money"]
            orig_hire(farm, private, board_size, hire_mult)
            if farm is farm0:
                cost = m_pre - farm["money"]
                hires_cost += cost
                hires_count += 1
                
        def hooked_buy_land(farm, board_size):
            nonlocal land_cost, land_count
            m_pre = farm["money"]
            orig_buy_land(farm, board_size)
            if farm is farm0:
                cost = m_pre - farm["money"]
                land_cost += cost
                land_count += 1
                
        kg._commit_unit = hooked_commit
        kg._do_hire = hooked_hire
        kg._do_buy_land = hooked_buy_land
        try:
            return orig_process_market(state, env_inner)
        finally:
            kg._commit_unit = orig_commit
            kg._do_hire = orig_hire
            kg._do_buy_land = orig_buy_land

    kg._process_market = hooked_process_market
    
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        opp_fn = kaggle_environments.environments['kaggriculture']['agents'][opp_name]
        env.run([agent_fn, opp_fn])
    finally:
        kg._process_market = orig_process_market
        
    final_reward = env.steps[-1][0]['reward']
    
    # Categorize revenue
    crop_items = ("MELON", "STRAWBERRY", "WHEAT", "TOMATO", "CARROT")
    livestock_items = ("MILK", "WOOL", "EGG", "FERTILIZER")
    
    crop_rev = sum(sales_by_item.get(it, {}).get("revenue", 0.0) for it in crop_items)
    live_rev = sum(sales_by_item.get(it, {}).get("revenue", 0.0) for it in livestock_items)
    total_rev = crop_rev + live_rev
    
    total_purchase_cost = sum(d["cost"] for d in purchases_by_item.values())
    total_expenses = total_purchase_cost + hires_cost + land_cost
    net_profit = total_rev - total_expenses
    
    return {
        "final_reward": final_reward,
        "crop_revenue": crop_rev,
        "livestock_revenue": live_rev,
        "total_revenue": total_rev,
        "sales": sales_by_item,
        "purchases": purchases_by_item,
        "hires_cost": hires_cost,
        "hires_count": hires_count,
        "land_cost": land_cost,
        "land_count": land_count,
        "total_expenses": total_expenses,
        "net_profit": net_profit
    }

if __name__ == '__main__':
    seeds = [42, 100, 2024, 104816794, 104817623]
    print(f"Running Exact Engine Hook Accounting across {len(seeds)} seeds...")
    
    v2_results = []
    prime_results = []
    
    for s in seeds:
        v2_r = run_exact_accounting(v2_agent, "V2 Baseline", s)
        prime_r = run_exact_accounting(prime_agent, "CL-Aethel Prime", s)
        v2_results.append(v2_r)
        prime_results.append(prime_r)
        print(f"Seed {s}: V2=${v2_r['final_reward']:,.0f} | Prime=${prime_r['final_reward']:,.0f} | Gap=${v2_r['final_reward']-prime_r['final_reward']:,.0f}")
        
    print("\n" + "="*80)
    print("EXACT MATHEMATICAL ENGINE ACCOUNTING (MEAN OVER 5 SEEDS)")
    print("="*80)
    v2_reward = np.mean([r['final_reward'] for r in v2_results])
    prime_reward = np.mean([r['final_reward'] for r in prime_results])
    gap = v2_reward - prime_reward
    print(f"V2 Mean Final Bank:    ${v2_reward:,.1f}")
    print(f"Prime Mean Final Bank: ${prime_reward:,.1f}")
    print(f"Total Gap:             ${gap:,.1f}\n")
    
    v2_crop = np.mean([r['crop_revenue'] for r in v2_results])
    prime_crop = np.mean([r['crop_revenue'] for r in prime_results])
    print(f"Crop Revenue:      V2=${v2_crop:,.1f} | Prime=${prime_crop:,.1f} | Delta=${v2_crop - prime_crop:,.1f} ({(v2_crop-prime_crop)/gap*100:.1f}%)")
    
    v2_live = np.mean([r['livestock_revenue'] for r in v2_results])
    prime_live = np.mean([r['livestock_revenue'] for r in prime_results])
    print(f"Livestock Revenue: V2=${v2_live:,.1f} | Prime=${prime_live:,.1f} | Delta=${v2_live - prime_live:,.1f} ({(v2_live-prime_live)/gap*100:.1f}%)")
    
    v2_exp = np.mean([r['total_expenses'] for r in v2_results])
    prime_exp = np.mean([r['total_expenses'] for r in prime_results])
    print(f"Total Expenses:    V2=${v2_exp:,.1f} | Prime=${prime_exp:,.1f} | Delta=${v2_exp - prime_exp:,.1f}")
    
    print("\n--- PER-PRODUCT REVENUE & VOLUME ---")
    all_products = ["MELON", "STRAWBERRY", "WHEAT", "MILK", "WOOL", "FERTILIZER"]
    for p in all_products:
        v2_p_rev = np.mean([r['sales'].get(p, {}).get("revenue", 0.0) for r in v2_results])
        prime_p_rev = np.mean([r['sales'].get(p, {}).get("revenue", 0.0) for r in prime_results])
        v2_p_u = np.mean([r['sales'].get(p, {}).get("units", 0.0) for r in v2_results])
        prime_p_u = np.mean([r['sales'].get(p, {}).get("units", 0.0) for r in prime_results])
        d_rev = v2_p_rev - prime_p_rev
        pct = (d_rev / gap) * 100 if gap else 0
        print(f"  {p:<12}: V2=${v2_p_rev:>9,.1f} ({v2_p_u:>5.1f}u) | Prime=${prime_p_rev:>9,.1f} ({prime_p_u:>5.1f}u) | Delta=${d_rev:>9,.1f} ({pct:>5.1f}%)")
        
    print("\n--- EXPENSE BREAKDOWN ---")
    v2_hires = np.mean([r['hires_cost'] for r in v2_results])
    prime_hires = np.mean([r['hires_cost'] for r in prime_results])
    print(f"  Hiring Costs: V2=${v2_hires:>9,.1f} | Prime=${prime_hires:>9,.1f} | Delta=${v2_hires - prime_hires:>9,.1f}")
    
    # Save exact results
    summary = {
        "v2_reward": v2_reward,
        "prime_reward": prime_reward,
        "gap": gap,
        "v2_crop": v2_crop,
        "prime_crop": prime_crop,
        "crop_delta": v2_crop - prime_crop,
        "v2_live": v2_live,
        "prime_live": prime_live,
        "live_delta": v2_live - prime_live,
        "v2_expenses": v2_exp,
        "prime_expenses": prime_exp,
    }
    with open("scratch/phase1_exact_accounting.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved exact accounting to scratch/phase1_exact_accounting.json")
