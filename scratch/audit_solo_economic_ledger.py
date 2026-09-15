"""
Detailed Solo Economic Ledger Auditor
Tracks all capital, labor, crops, livestock, market, land metrics step by step.
"""
import sys, os, json
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

from kaggle_environments import make
from candidates.declarative_backbone.params import V54_PRIOR
from candidates.declarative_backbone.compiler import DeclarativeBackboneCompiler

def run_audited_game(seed=2003, opp_fn=None):
    comp = DeclarativeBackboneCompiler(V54_PRIOR)
    
    # Tracking ledgers
    ledger = {
        "seed": seed,
        "daily_cash": {},
        "spending_by_category": {
            "HIRE": 0, "BUY_LAND": 0, "BUY_ANIMAL": 0, "BUY_FEED": 0, "BUY_SEEDS": 0
        },
        "sales_by_category": {},
        "workers_by_day": {},
        "hire_costs_by_day": {},
        "action_counts": {},
        "seeds_bought": {},
        "seeds_planted": {},
        "crops_harvested": {},
        "animals_bought": {},
        "animals_placed": {},
        "animal_care_counts": {},
        "animal_feed_counts": {},
        "fert_collected": 0,
        "market_orders_submitted": 0,
        "market_orders_succeeded": 0,
        "market_orders_failed": 0,
        "land_unlock_steps": [],
        "terminal_stranded_inventory": {},
    }
    
    if opp_fn is None:
        def opp_fn(obs, cfg=None):
            return {"market": [], "farmer": ["PASS"], "hands": []}

    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    obs = env.reset()
    prev_money = obs[0].observation.farms[0]["money"]
    prev_quads = len(obs[0].observation.farms[0]["unlocked_quadrants"])
    
    for step_idx in range(720):
        # We wrap the backbone call to inspect decisions
        action0 = comp(obs[0].observation)
        action1 = opp_fn(obs[1].observation)
        
        # Track actions submitted
        all_actions = [action0.get("farmer", ["PASS"])] + action0.get("hands", [])
        for act in all_actions:
            op = act[0] if act else "PASS"
            ledger["action_counts"][op] = ledger["action_counts"].get(op, 0) + 1
            if op == "PLANT":
                crop = act[1] if len(act) > 1 else "UNKNOWN"
                ledger["seeds_planted"][crop] = ledger["seeds_planted"].get(crop, 0) + 1
            elif op == "PLACE":
                an = act[1] if len(act) > 1 else "UNKNOWN"
                ledger["animals_placed"][an] = ledger["animals_placed"].get(an, 0) + 1
            elif op == "FEED":
                ledger["animal_feed_counts"]["FEED"] = ledger["animal_feed_counts"].get("FEED", 0) + 1
            elif op == "CARE":
                ledger["animal_care_counts"]["CARE"] = ledger["animal_care_counts"].get("CARE", 0) + 1
            elif op == "COLLECT_FERTILIZER":
                ledger["fert_collected"] += 1
            elif op == "HARVEST":
                ledger["crops_harvested"]["HARVEST_OP"] = ledger["crops_harvested"].get("HARVEST_OP", 0) + 1
        
        # Track market orders submitted
        m_orders = action0.get("market", [])
        ledger["market_orders_submitted"] += len(m_orders)
        
        # Advance env
        obs = env.step([action0, action1])
        if env.done:
            break
        
        farm0 = obs[0].observation.farms[0]
        curr_money = farm0["money"]
        day = obs[0].observation.day
        hour = obs[0].observation.hour
        
        # Check land expansion
        curr_quads = len(farm0["unlocked_quadrants"])
        if curr_quads > prev_quads:
            ledger["land_unlock_steps"].append((step_idx, curr_quads))
            ledger["spending_by_category"]["BUY_LAND"] += [1000, 2000, 4000][prev_quads - 1]
            prev_quads = curr_quads
            
        # Daily snapshots at hour 0 or end of day
        if hour == 23 or step_idx == 719:
            ledger["daily_cash"][day] = curr_money
            ledger["workers_by_day"][day] = farm0["hires_today"]
            
        # Track spending/sales through market diffs
        for order in m_orders:
            op = order[0]
            if op == "HIRE":
                pass # counted via hires
            elif op == "BUY_ANIMAL":
                an = order[1]
                ledger["animals_bought"][an] = ledger["animals_bought"].get(an, 0) + 1
                cost = 600 if an == "COW" else 500
                ledger["spending_by_category"]["BUY_ANIMAL"] += cost
            elif op == "BUY_PRODUCT" and order[1] == "WHEAT":
                qty = order[2] if len(order) > 2 else 1
                # approx price
                ledger["spending_by_category"]["BUY_FEED"] += qty * 25
            elif op == "BUY_SEED":
                sd = order[1]
                qty = order[2] if len(order) > 2 else 1
                ledger["seeds_bought"][sd] = ledger["seeds_bought"].get(sd, 0) + qty
                seed_cost = {"WHEAT": 10, "CARROT": 20, "MELON": 80, "STRAWBERRY": 100}.get(sd, 0)
                ledger["spending_by_category"]["BUY_SEEDS"] += qty * seed_cost
            elif op == "SELL":
                prod = order[1]
                qty = order[2] if len(order) > 2 else 1
                ledger["sales_by_category"][prod] = ledger["sales_by_category"].get(prod, 0) + qty

    # Terminal state
    final_farm = obs[0].observation.farms[0]
    final_private = obs[0].observation.private
    ledger["final_reward"] = obs[0].reward
    ledger["terminal_shed"] = final_private.get("shed", {})
    ledger["terminal_seeds"] = final_private.get("seeds", {})
    
    # Calculate hire spending
    total_hire_cost = 0
    for day, n_hires in ledger["workers_by_day"].items():
        # fib sum
        a, b = 1, 1
        day_cost = 0
        for _ in range(n_hires):
            day_cost += a
            a, b = b, a + b
        total_hire_cost += day_cost
    ledger["spending_by_category"]["HIRE"] = total_hire_cost

    return ledger

if __name__ == "__main__":
    ledger = run_audited_game(2003)
    print("=== SEED 2003 SOLO LEDGER ===")
    print(f"Final Reward: {ledger['final_reward']}")
    print("\n--- Spending By Category ---")
    for k, v in ledger["spending_by_category"].items():
        print(f"  {k:15s}: {v:,.0f}")
    print("\n--- Sales By Category (quantities) ---")
    for k, v in ledger["sales_by_category"].items():
        print(f"  {k:15s}: {v}")
    print("\n--- Seeds Bought ---")
    for k, v in ledger["seeds_bought"].items():
        print(f"  {k:15s}: {v}")
    print("\n--- Seeds Planted ---")
    for k, v in ledger["seeds_planted"].items():
        print(f"  {k:15s}: {v}")
    print("\n--- Animals Bought vs Placed ---")
    print(f"  Bought: {ledger['animals_bought']}")
    print(f"  Placed: {ledger['animals_placed']}")
    print("\n--- Land Unlocks ---")
    print(f"  {ledger['land_unlock_steps']}")
    print("\n--- Action Counts ---")
    for k, v in sorted(ledger["action_counts"].items(), key=lambda x: -x[1]):
        print(f"  {k:20s}: {v}")
    print("\n--- Terminal Shed & Seeds ---")
    print(f"  Shed: {ledger['terminal_shed']}")
    print(f"  Seeds: {ledger['terminal_seeds']}")
    print("\n--- Daily Workers & Cash Sample ---")
    for d in [0, 1, 2, 3, 5, 10, 15, 20, 25, 29]:
        print(f"  Day {d:2d}: Cash={ledger['daily_cash'].get(d, 0):7.0f}, Workers={ledger['workers_by_day'].get(d, 0)}")
