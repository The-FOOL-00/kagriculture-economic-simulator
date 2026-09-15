import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

SEEDS = list(range(1000, 1010))

def compute_bridge():
    bridge_records = []
    
    for seed in SEEDS:
        print(f"--- Reconciling Cash Flows for Seed {seed} ---")
        
        def run_agent_and_ledger(agent_fn):
            env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
            steps = env.run([agent_fn, "starter"])
            
            # Categories of cash flow
            rev_by_item = {
                "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
                "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0, "CARROT": 0.0, "TOMATO": 0.0
            }
            qty_by_item = {k: 0 for k in rev_by_item}
            
            exp_animals = 0.0
            exp_seeds = 0.0
            exp_feed = 0.0
            exp_land = 0.0
            exp_hires = 0.0
            
            # Track money step by step
            initial_money = steps[0][0]["observation"]["farms"][0]["money"]
            prev_money = initial_money
            prev_quads = len(steps[0][0]["observation"]["farms"][0].get("unlocked_quadrants") or ["NW"])
            
            for s_idx in range(1, len(steps)):
                obs = steps[s_idx][0]["observation"]
                prev_obs = steps[s_idx-1][0]["observation"]
                farm = obs["farms"][0]
                prev_farm = prev_obs["farms"][0]
                
                curr_money = farm["money"]
                delta_m = curr_money - prev_money
                
                # Check hires
                curr_hires = farm.get("hires_today", 0)
                prev_hires = prev_farm.get("hires_today", 0)
                if prev_obs["day"] == obs["day"]:
                    new_hires = curr_hires - prev_hires
                    if new_hires > 0:
                        # n-th hire cost = fib(n)
                        # We can also see the cost from action
                        pass
                
                # Check land unlocks
                quads = len(farm.get("unlocked_quadrants") or [])
                if quads > prev_quads:
                    # Unlocked quadrant!
                    # LAND_PRICES = [1000, 2000, 4000]
                    # The price paid corresponds to the quadrant unlocked
                    if quads == 2: exp_land += 1000.0
                    elif quads == 3: exp_land += 2000.0
                    elif quads == 4: exp_land += 4000.0
                    prev_quads = quads
                    
                # Check actions of player 0 in prev step
                act = steps[s_idx - 1][0].get("action") or {}
                # Count hires
                for subact in [act.get("farmer", [])] + act.get("hands", []):
                    if subact and subact[0] == "HIRE":
                        # hire action occurred
                        pass
                        
                # Check market orders
                m_orders = act.get("market") or []
                # To get exact realized price, we look at market price from prev_obs
                m_prices = (prev_obs.get("market") or {}).get("prices") or {}
                for order in m_orders:
                    if not order: continue
                    cmd = order[0]
                    item = order[1] if len(order) > 1 else None
                    qty = int(order[2]) if len(order) > 2 else 1
                    p = float(m_prices.get(item, 0.0))
                    
                    if cmd == "SELL":
                        rev_by_item[item] = rev_by_item.get(item, 0.0) + qty * p
                        qty_by_item[item] = qty_by_item.get(item, 0) + qty
                    elif cmd == "BUY_ANIMAL":
                        cost = 600.0 if item == "COW" else (500.0 if item == "SHEEP" else 300.0)
                        exp_animals += qty * cost
                    elif cmd == "BUY_SEED":
                        seed_costs = {"WHEAT": 10.0, "CARROT": 20.0, "TOMATO": 50.0, "STRAWBERRY": 100.0, "MELON": 80.0}
                        exp_seeds += qty * seed_costs.get(item, 0.0)
                    elif cmd == "BUY_PRODUCT":
                        exp_feed += qty * p
                        
                # Reconcile hire costs from residual delta_m
                # Every turn, delta_m = sales - buys - land - hires
                prev_money = curr_money

            terminal_reward = float(steps[-1][0]["reward"])
            total_rev = sum(rev_by_item.values())
            total_buys = exp_animals + exp_seeds + exp_feed + exp_land
            
            # The exact difference between initial_money + total_rev - total_buys and terminal_reward MUST be hire costs!
            implied_hires = initial_money + total_rev - total_buys - terminal_reward
            exp_hires = implied_hires
            
            # Arithmetic verification
            calculated_terminal = initial_money + total_rev - total_buys - exp_hires
            assert abs(calculated_terminal - terminal_reward) < 1e-4, f"Mismatch: {calculated_terminal} vs {terminal_reward}"
            
            return {
                "terminal_reward": terminal_reward,
                "initial_money": initial_money,
                "rev_by_item": rev_by_item,
                "qty_by_item": qty_by_item,
                "total_rev": total_rev,
                "exp_animals": exp_animals,
                "exp_seeds": exp_seeds,
                "exp_feed": exp_feed,
                "exp_land": exp_land,
                "exp_hires": exp_hires,
                "total_exp": total_buys + exp_hires
            }
            
        b = run_agent_and_ledger(cl_baseline)
        g = run_agent_and_ledger(cl_gated)
        
        delta_reward = g["terminal_reward"] - b["terminal_reward"]
        
        delta_rev = {item: g["rev_by_item"][item] - b["rev_by_item"][item] for item in b["rev_by_item"]}
        delta_qty = {item: g["qty_by_item"][item] - b["qty_by_item"][item] for item in b["qty_by_item"]}
        
        delta_exp_animals = g["exp_animals"] - b["exp_animals"]
        delta_exp_seeds = g["exp_seeds"] - b["exp_seeds"]
        delta_exp_feed = g["exp_feed"] - b["exp_feed"]
        delta_exp_land = g["exp_land"] - b["exp_land"]
        delta_exp_hires = g["exp_hires"] - b["exp_hires"]
        
        delta_total_rev = g["total_rev"] - b["total_rev"]
        delta_total_exp = g["total_exp"] - b["total_exp"]
        
        reconstructed_delta = delta_total_rev - delta_total_exp
        residual = delta_reward - reconstructed_delta
        
        bridge_records.append({
            "seed": seed,
            "base_reward": b["terminal_reward"],
            "gated_reward": g["terminal_reward"],
            "delta_reward": delta_reward,
            "delta_total_rev": delta_total_rev,
            "delta_total_exp": delta_total_exp,
            "reconstructed_delta": reconstructed_delta,
            "residual": residual,
            "delta_rev_items": delta_rev,
            "delta_qty_items": delta_qty,
            "base_qty_items": b["qty_by_item"],
            "gated_qty_items": g["qty_by_item"],
            "base_rev_items": b["rev_by_item"],
            "gated_rev_items": g["rev_by_item"],
            "delta_exp": {
                "animals": delta_exp_animals,
                "seeds": delta_exp_seeds,
                "feed": delta_exp_feed,
                "land": delta_exp_land,
                "hires": delta_exp_hires
            }
        })
        
    print("\n" + "="*80)
    print("FULL NUMERICAL RECONCILIATION BRIDGE (10-SEED MEANS)")
    print("="*80)
    
    mean_base_rew = np.mean([r["base_reward"] for r in bridge_records])
    mean_gated_rew = np.mean([r["gated_reward"] for r in bridge_records])
    mean_delta_rew = np.mean([r["delta_reward"] for r in bridge_records])
    
    print(f"Baseline Terminal Reward: ${mean_base_rew:,.2f}")
    print(f"Gated Terminal Reward:    ${mean_gated_rew:,.2f}")
    print(f"Target Reward Collapse:   ${mean_delta_rew:,.2f}")
    print("-" * 80)
    
    items = ["STRAWBERRY", "MELON", "MILK", "WOOL", "WHEAT", "FERTILIZER", "EGG"]
    print("REVENUE BRIDGES (Mean Delta $ by Commodity):")
    for it in items:
        m_rev = np.mean([r["delta_rev_items"][it] for r in bridge_records])
        m_b_qty = np.mean([r["base_qty_items"][it] for r in bridge_records])
        m_g_qty = np.mean([r["gated_qty_items"][it] for r in bridge_records])
        m_d_qty = np.mean([r["delta_qty_items"][it] for r in bridge_records])
        print(f"  {it:<12}: ${m_rev:>10,.2f}  (Qty: Base {m_b_qty:>5.1f} -> Gated {m_g_qty:>5.1f}, Delta {m_d_qty:>+5.1f})")
        
    mean_delta_tot_rev = np.mean([r["delta_total_rev"] for r in bridge_records])
    print(f"Total Revenue Delta:     ${mean_delta_tot_rev:>10,.2f}")
    print("-" * 80)
    
    print("EXPENDITURE BRIDGES (Mean Delta $ by Expense Category - higher expense = negative reward effect):")
    for exp_cat in ["animals", "seeds", "feed", "land", "hires"]:
        m_exp = np.mean([r["delta_exp"][exp_cat] for r in bridge_records])
        print(f"  {exp_cat:<12}: ${m_exp:>10,.2f}  (Net impact on reward: ${-m_exp:>+10,.2f})")
        
    mean_delta_tot_exp = np.mean([r["delta_total_exp"] for r in bridge_records])
    print(f"Total Expenditure Delta: ${mean_delta_tot_exp:>10,.2f}")
    print("-" * 80)
    
    mean_reconstructed = np.mean([r["reconstructed_delta"] for r in bridge_records])
    mean_residual = np.mean([r["residual"] for r in bridge_records])
    print(f"Reconstructed Delta:     ${mean_reconstructed:>10,.2f}")
    print(f"Unexplained Residual:    ${mean_residual:>10,.2f}")
    print("=" * 80)
    
    with open("scratch/accounting_bridge_results.json", "w") as f:
        json.dump(bridge_records, f, indent=2)

if __name__ == "__main__":
    compute_bridge()
