import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

SEEDS = list(range(1000, 1010))

def audit_seeds():
    results = {}
    
    for seed in SEEDS:
        print(f"--- Running Seed {seed} ---")
        env_base = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_base = env_base.run([cl_baseline, "starter"])
        
        env_gated = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_gated = env_gated.run([cl_gated, "starter"])
        
        def process_run(steps, name):
            # Track shops unlocked
            # Track strawberry prices throughout 720 steps
            # Track every market transaction
            # Track reward and cash flow
            straw_prices = []
            straw_invs = []
            fert_prices = []
            fert_invs = []
            transactions = []
            town_shops_by_day = {}
            
            p0_sales = {}
            p0_buys = {}
            p1_sales = {}
            p1_buys = {}
            
            for s_idx in range(len(steps)):
                obs = steps[s_idx][0]["observation"]
                day = obs["day"]
                hour = obs["hour"]
                step = obs["step"]
                market = obs.get("market") or {}
                m_inv = market.get("inventory") or {}
                m_pr = market.get("prices") or {}
                town = obs.get("town") or {}
                unlocked_shops = list(town.get("unlocked_shops") or [])
                town_shops_by_day[day] = unlocked_shops
                
                sp = m_pr.get("STRAWBERRY")
                si = m_inv.get("STRAWBERRY")
                fp = m_pr.get("FERTILIZER")
                fi = m_inv.get("FERTILIZER")
                
                straw_prices.append((step, day, hour, sp, si))
                fert_prices.append((step, day, hour, fp, fi))
                
                # Check actions executed in previous step
                if s_idx > 0:
                    prev_step_data = steps[s_idx - 1]
                    # Player 0 action
                    act0 = prev_step_data[0].get("action") or {}
                    m_orders0 = act0.get("market") or []
                    for order in m_orders0:
                        if not order: continue
                        cmd = order[0]
                        item = order[1] if len(order) > 1 else None
                        qty = order[2] if len(order) > 2 else 1
                        if cmd == "SELL":
                            p0_sales[item] = p0_sales.get(item, 0) + qty
                            transactions.append({
                                "step": step - 1, "day": day, "hour": hour, "player": 0,
                                "type": "SELL", "item": item, "qty": qty,
                                "price": sp if item == "STRAWBERRY" else (fp if item == "FERTILIZER" else m_pr.get(item))
                            })
                        elif cmd in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
                            p0_buys[item] = p0_buys.get(item, 0) + qty
                            transactions.append({
                                "step": step - 1, "day": day, "hour": hour, "player": 0,
                                "type": cmd, "item": item, "qty": qty,
                                "price": m_pr.get(item)
                            })
                            
                    # Player 1 (starter) action
                    act1 = prev_step_data[1].get("action") or {}
                    m_orders1 = act1.get("market") or []
                    for order in m_orders1:
                        if not order: continue
                        cmd = order[0]
                        item = order[1] if len(order) > 1 else None
                        qty = order[2] if len(order) > 2 else 1
                        if cmd == "SELL":
                            p1_sales[item] = p1_sales.get(item, 0) + qty
                        elif cmd in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
                            p1_buys[item] = p1_buys.get(item, 0) + qty
            
            terminal_obs = steps[-1][0]["observation"]
            terminal_money = terminal_obs["farms"][0]["money"]
            terminal_reward = steps[-1][0]["reward"]
            
            return {
                "terminal_reward": terminal_reward,
                "terminal_money": terminal_money,
                "town_shops_final": town_shops_by_day[29],
                "straw_prices": straw_prices,
                "fert_prices": fert_prices,
                "transactions": transactions,
                "p0_sales": p0_sales,
                "p0_buys": p0_buys,
                "p1_sales": p1_sales,
                "p1_buys": p1_buys
            }
            
        base_res = process_run(steps_base, "baseline")
        gated_res = process_run(steps_gated, "gated")
        
        # Compare strawberry prices
        base_straw_p = [p[3] for p in base_res["straw_prices"]]
        gated_straw_p = [p[3] for p in gated_res["straw_prices"]]
        
        base_min_p, base_max_p, base_avg_p = min(base_straw_p), max(base_straw_p), np.mean(base_straw_p)
        gated_min_p, gated_max_p, gated_avg_p = min(gated_straw_p), max(gated_straw_p), np.mean(gated_straw_p)
        
        diff_reward = gated_res["terminal_reward"] - base_res["terminal_reward"]
        
        print(f"Seed {seed}:")
        print(f"  Base Reward: ${base_res['terminal_reward']:,.1f} | Gated Reward: ${gated_res['terminal_reward']:,.1f} | Delta: ${diff_reward:,.1f}")
        print(f"  Base Strawberry Price: avg=${base_avg_p:.1f}, min=${base_min_p}, max=${base_max_p}")
        print(f"  Gated Strawberry Price: avg=${gated_avg_p:.1f}, min=${gated_min_p}, max=${gated_max_p}")
        print(f"  Base Shops: {base_res['town_shops_final']}")
        print(f"  Gated Shops: {gated_res['town_shops_final']}")
        print(f"  Shops Match?: {base_res['town_shops_final'] == gated_res['town_shops_final']}")
        print(f"  Base P0 Sales: {base_res['p0_sales']}")
        print(f"  Gated P0 Sales: {gated_res['p0_sales']}")
        print(f"  P1 (Starter) Sales Base: {base_res['p1_sales']} | Gated: {gated_res['p1_sales']}")
        
        results[seed] = {
            "base_reward": base_res["terminal_reward"],
            "gated_reward": gated_res["terminal_reward"],
            "delta_reward": diff_reward,
            "base_straw_p_stats": (base_min_p, base_max_p, base_avg_p),
            "gated_straw_p_stats": (gated_min_p, gated_max_p, gated_avg_p),
            "shops_match": base_res["town_shops_final"] == gated_res["town_shops_final"],
            "base_shops": base_res["town_shops_final"],
            "gated_shops": gated_res["town_shops_final"],
            "base_sales": base_res["p0_sales"],
            "gated_sales": gated_res["p0_sales"],
            "base_transactions": base_res["transactions"],
            "gated_transactions": gated_res["transactions"]
        }
        
    with open("scratch/audit_pricing_results.json", "w") as f:
        # Don't dump transactions to json if too big, dump summary
        summary = {
            k: {
                "base_reward": v["base_reward"],
                "gated_reward": v["gated_reward"],
                "delta_reward": v["delta_reward"],
                "base_straw_p_stats": v["base_straw_p_stats"],
                "gated_straw_p_stats": v["gated_straw_p_stats"],
                "shops_match": v["shops_match"],
                "base_shops": v["base_shops"],
                "gated_shops": v["gated_shops"],
                "base_sales": v["base_sales"],
                "gated_sales": v["gated_sales"]
            }
            for k, v in results.items()
        }
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    audit_seeds()
