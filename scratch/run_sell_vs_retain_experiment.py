import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated_sell
from candidates.candidate_cl_fert_gated_retain import agent as cl_gated_retain

SEEDS = list(range(1000, 1010))

def run_experiment():
    arms = {
        "Baseline": cl_baseline,
        "Gated_Sell": cl_gated_sell,
        "Gated_Retain": cl_gated_retain
    }
    
    results = {arm: {} for arm in arms}
    
    for seed in SEEDS:
        print(f"\n================ Running Seed {seed} ================")
        for arm_name, agent_fn in arms.items():
            env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
            steps = env.run([agent_fn, "starter"])
            
            straw_harvested = 0
            fert_collected = 0
            fert_applied = 0
            
            straw_prices = []
            straw_sold = 0
            straw_rev = 0.0
            fert_sold = 0
            fert_rev = 0.0
            
            max_shed_fill = 0
            
            for s_idx in range(1, len(steps)):
                prev_obs = steps[s_idx-1][0]["observation"]
                curr_obs = steps[s_idx][0]["observation"]
                
                # Market prices
                sp = curr_obs.get("market", {}).get("prices", {}).get("STRAWBERRY", 120)
                straw_prices.append(sp)
                
                # Check shed fullness
                shed = curr_obs["private"]["shed"]
                shed_fill = sum(shed.values())
                if shed_fill > max_shed_fill:
                    max_shed_fill = shed_fill
                    
                # Check harvests & fertilizer
                act = steps[s_idx-1][0].get("action") or {}
                m_prices = prev_obs.get("market", {}).get("prices", {})
                
                # Check worker actions
                all_worker_acts = [act.get("farmer", [])] + act.get("hands", [])
                for wact in all_worker_acts:
                    if not wact: continue
                    if wact[0] == "COLLECT_FERTILIZER":
                        fert_collected += 1
                    elif wact[0] == "FERTILIZE":
                        fert_applied += 1
                    elif wact[0] == "HARVEST":
                        # Check tile kind in prev_obs
                        # We can also detect physical produce increase
                        pass
                
                # Measure physical strawberry harvest by delta in total strawberry in system + sales
                # Or count ripe strawberries picked
                # Let's count from farm tiles yield unit decrements
                prev_tiles = prev_obs["farms"][0]["tiles"]
                curr_tiles = curr_obs["farms"][0]["tiles"]
                for r in range(len(prev_tiles)):
                    for c in range(len(prev_tiles[r])):
                        pt = prev_tiles[r][c]
                        ct = curr_tiles[r][c]
                        if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                            py = int(pt.get("yield_units", 0) or 0)
                            cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) else 0
                            # If worker was on tile and action was HARVEST
                            # Harvest gives 1 unit per action
                            for wpos, wact in zip([prev_obs["farms"][0]["farmer"]] + prev_obs["farms"][0]["hands"], all_worker_acts):
                                if tuple(wpos) == (c, r) and wact and wact[0] == "HARVEST":
                                    straw_harvested += 1
                                    
                # Market transactions
                for order in act.get("market") or []:
                    if not order: continue
                    cmd, item = order[0], order[1] if len(order) > 1 else None
                    qty = int(order[2]) if len(order) > 2 else 1
                    if cmd == "SELL":
                        p = float(m_prices.get(item, 0))
                        if item == "STRAWBERRY":
                            straw_sold += qty
                            straw_rev += qty * p
                        elif item == "FERTILIZER":
                            fert_sold += qty
                            fert_rev += qty * p
                            
            term_obs = steps[-1][0]["observation"]
            term_reward = float(steps[-1][0]["reward"])
            term_money = float(term_obs["farms"][0]["money"])
            term_shed = dict(term_obs["private"]["shed"])
            term_fert_shed = int(term_shed.get("FERTILIZER", 0) or 0)
            term_fert_pockets = sum(int(inv.get("FERTILIZER", 0) or 0) for inv in term_obs["private"]["inventories"])
            
            arm_data = {
                "reward": term_reward,
                "money": term_money,
                "straw_harvested": straw_harvested,
                "straw_sold": straw_sold,
                "straw_rev": straw_rev,
                "straw_avg_p": float(np.mean(straw_prices)),
                "straw_min_p": int(min(straw_prices)),
                "straw_max_p": int(max(straw_prices)),
                "fert_collected": fert_collected,
                "fert_applied": fert_applied,
                "fert_sold": fert_sold,
                "fert_rev": fert_rev,
                "fert_remaining": term_fert_shed + term_fert_pockets,
                "max_shed_fill": max_shed_fill
            }
            results[arm_name][seed] = arm_data
            print(f"  {arm_name:<14}: Reward=${term_reward:>9,.1f} | StrawHarvest={straw_harvested:>3} | StrawSold={straw_sold:>3} (${straw_rev:>7,.1f}, p_avg=${arm_data['straw_avg_p']:.1f}, min=${arm_data['straw_min_p']}) | Fert: App={fert_applied:>2}, Sold={fert_sold:>3}, Rem={term_fert_shed+term_fert_pockets:>2} | MaxShed={max_shed_fill}")

    with open("scratch/sell_vs_retain_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "="*90)
    print("COUNTERFACTUAL COMPARISON SUMMARY (10-SEED MEANS)")
    print("="*90)
    print(f"{'Metric':<25} | {'Baseline':>18} | {'Gated + Sell Fert':>18} | {'Gated + Retain Fert':>18}")
    print("-" * 90)
    
    metrics = [
        ("Terminal Reward ($)", "reward", "${:,.1f}"),
        ("Strawberry Harvested (u)", "straw_harvested", "{:.2f}"),
        ("Strawberry Sold (u)", "straw_sold", "{:.2f}"),
        ("Strawberry Realized Rev ($)", "straw_rev", "${:,.1f}"),
        ("Strawberry Avg Price ($)", "straw_avg_p", "${:.1f}"),
        ("Strawberry Min Price ($)", "straw_min_p", "${:.1f}"),
        ("Fertilizer Collected (u)", "fert_collected", "{:.2f}"),
        ("Fertilizer Applied (u)", "fert_applied", "{:.2f}"),
        ("Fertilizer Sold (u)", "fert_sold", "{:.2f}"),
        ("Fertilizer Realized Rev ($)", "fert_rev", "${:,.1f}"),
        ("Fertilizer Remaining (u)", "fert_remaining", "{:.2f}"),
        ("Max Shed Inventory (u)", "max_shed_fill", "{:.1f}"),
    ]
    
    for label, key, fmt in metrics:
        v_base = np.mean([results["Baseline"][s][key] for s in SEEDS])
        v_sell = np.mean([results["Gated_Sell"][s][key] for s in SEEDS])
        v_retain = np.mean([results["Gated_Retain"][s][key] for s in SEEDS])
        print(f"{label:<25} | {fmt.format(v_base):>18} | {fmt.format(v_sell):>18} | {fmt.format(v_retain):>18}")
    print("="*90)

if __name__ == "__main__":
    run_experiment()
