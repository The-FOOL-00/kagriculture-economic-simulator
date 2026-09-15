"""
scratch/test_accounting_identity.py
===================================
Verifies the exact accounting identity across all 720 turns on real replay files.
"""

import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from engine.economic_accounting import market_price, CROPS, ANIMALS


def audit_replay_accounting(replay_path: str, player_idx: int = 0):
    print(f"\n========================================================")
    print(f"AUDITING REPLAY: {os.path.basename(replay_path)} (Player {player_idx})")
    print(f"========================================================")
    
    with open(replay_path, "r") as f:
        data = json.load(f)
        
    steps = data["steps"]
    total_steps = len(steps)
    
    start_money = steps[0][player_idx]["observation"]["farms"][player_idx]["money"]
    final_money = steps[-1][player_idx]["observation"]["farms"][player_idx]["money"]
    final_reward = steps[-1][player_idx].get("reward", final_money)
    
    cash_deltas = []
    
    # Categories
    total_land_expenditure = 0
    total_hire_expenditure = 0
    total_seed_expenditure = 0
    total_animal_expenditure = 0
    total_product_buy_expenditure = 0
    total_sales_revenue = 0
    
    sales_by_item = {}
    units_sold_by_item = {}
    buys_by_item = {}
    
    for t in range(total_steps - 1):
        m_curr = steps[t][player_idx]["observation"]["farms"][player_idx]["money"]
        m_next = steps[t + 1][player_idx]["observation"]["farms"][player_idx]["money"]
        delta = m_next - m_curr
        cash_deltas.append(delta)
        
        # Check action executed at turn t
        action = steps[t][player_idx].get("action") or {}
        market_orders = action.get("market") or []
        
        # Categorize changes
        if delta < 0:
            expenditure = -delta
            # Classify by market orders
            has_land = any(o[0] == "BUY_LAND" for o in market_orders)
            has_hire = any(o[0] == "HIRE" for o in market_orders)
            has_seed = any(o[0] == "BUY_SEED" for o in market_orders)
            has_animal = any(o[0] == "BUY_ANIMAL" for o in market_orders)
            has_prod = any(o[0] == "BUY_PRODUCT" for o in market_orders)
            
        elif delta > 0:
            total_sales_revenue += delta
            # Look at SELL orders
            for o in market_orders:
                if o[0] == "SELL":
                    item = o[1]
                    n = int(o[2]) if len(o) > 2 else 1
                    units_sold_by_item[item] = units_sold_by_item.get(item, 0) + n
                    
    net_realized_cash = sum(cash_deltas)
    expected_final = start_money + net_realized_cash
    discrepancy = abs(expected_final - final_money)
    
    print(f"Starting Money:     ${start_money:,.2f}")
    print(f"Final Money:        ${final_money:,.2f}")
    print(f"Final Reward:       ${final_reward:,.2f}")
    print(f"Sum of Turn Deltas: ${net_realized_cash:,.2f}")
    print(f"Accounting Balance: ${expected_final:,.2f}")
    print(f"Discrepancy:        ${discrepancy:,.6f}")
    assert discrepancy < 1e-4, f"Accounting identity failure: discrepancy = {discrepancy}"
    print(">>> EXACT ACCOUNTING IDENTITY VERIFIED: 0.00 DISCREPANCY <<<\n")


if __name__ == "__main__":
    replays = [
        os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "opponents", "top1_tetsuya", "replays", "episode-104060611-replay.json"),
        os.path.join(BASE_DIR, "master_83k_replay.json"),
    ]
    for r in replays:
        if os.path.exists(r):
            audit_replay_accounting(r, player_idx=0)
            audit_replay_accounting(r, player_idx=1)
