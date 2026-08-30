import os
import sys
import json
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
apex_path = os.path.join(project_root, "agents", "apex_v2_frozen.py")
ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 50000}, debug=True)
env.run([apex_path, ctrl_path])

# Analyze the match steps
steps = env.steps

day0_melons = 0
cycle2_melons = 0
carrots_planted = 0
cows_bought = 0
sheep_bought = 0
geese_bought = 0
hands_hired = 0
wheat_bought = 0
emergency_sells = 0
batches_sold = []
fertilizer_collected = 0
fertilizer_sold = 0
shed_wheat_levels = []
daily_cash = []
daily_workers = []

for step_idx, step_data in enumerate(steps):
    obs0 = step_data[0].observation
    action0 = step_data[0].action or {}
    player_obs = obs0
    day = obs0.get("day", 0)
    hour = obs0.get("hour", 0)
    farms = obs0.get("farms", [])
    p0_farm = farms[0] if farms else {}
    private = obs0.get("private", {}) or {}
    shed = private.get("shed", {})
    
    if hour == 0:
        daily_cash.append((day, p0_farm.get("money", 0)))
        daily_workers.append((day, 1 + len(p0_farm.get("hands", []))))
        shed_wheat_levels.append((day, shed.get("WHEAT", 0)))

    # Inspect market orders
    market_orders = action0.get("market", [])
    for ord_item in market_orders:
        otype = ord_item[0]
        if otype == "BUY_SEED":
            stype, qty = ord_item[1], ord_item[2]
            if stype == "MELON":
                if day <= 2: day0_melons += qty
                elif 10 <= day <= 13: cycle2_melons += qty
            elif stype == "CARROT":
                carrots_planted += qty
        elif otype == "BUY_ANIMAL":
            atype, qty = ord_item[1], ord_item[2]
            if atype == "COW": cows_bought += qty
            elif atype == "SHEEP": sheep_bought += qty
            elif atype == "GOOSE": geese_bought += qty
        elif otype == "BUY_PRODUCT":
            ptype, qty = ord_item[1], ord_item[2]
            if ptype == "WHEAT": wheat_bought += qty
        elif otype == "HIRE":
            hands_hired += 1
        elif otype == "SELL":
            ptype, qty = ord_item[1], ord_item[2]
            batches_sold.append((day, hour, ptype, qty))
            if ptype == "FERTILIZER": fertilizer_sold += qty

# Final state
last_step = steps[-1]
final_cash = last_step[0].reward
ctrl_cash = last_step[1].reward

print("=" * 80)
print("RUNTIME CONFIGURATION TRACE & BEHAVIORAL VERIFICATION")
print("=" * 80)
print(f"Final Outcome: Apex Cash = ${final_cash:,.2f} vs Control = ${ctrl_cash:,.2f} (Margin: {final_cash - ctrl_cash:+,.2f})")
print("\n--- Animal Procurement ---")
print(f"Total Cows Bought:    {cows_bought} (Target: 8)")
print(f"Total Sheep Bought:   {sheep_bought} (Target: 4)")
print(f"Total Geese Bought:   {geese_bought} (Target: 0)")

print("\n--- Crop Allocations ---")
print(f"Day 0-2 Melons:       {day0_melons} (Target: 15)")
print(f"Cycle-2 Melons:       {cycle2_melons} (Target: 8)")
print(f"Secondary Carrots:    {carrots_planted}")

print("\n--- Logistics & Market ---")
print(f"Total Wheat Purchased:{wheat_bought}")
print(f"Max Shed Wheat Level: {max(s[1] for s in shed_wheat_levels)} (Target: 24 buffer)")
print(f"Avg Shed Wheat Level: {sum(s[1] for s in shed_wheat_levels)/len(shed_wheat_levels):.1f}")
print(f"Total Hands Hired:    {hands_hired}")
print(f"Total Market Batches: {len(batches_sold)}")
print(f"Sample Batches Sold:  {batches_sold[:8]}")

trace_summary = {
    "cows_bought": cows_bought,
    "sheep_bought": sheep_bought,
    "geese_bought": geese_bought,
    "day0_melons": day0_melons,
    "cycle2_melons": cycle2_melons,
    "wheat_bought": wheat_bought,
    "max_shed_wheat": max(s[1] for s in shed_wheat_levels),
    "final_cash": final_cash,
    "ctrl_cash": ctrl_cash,
    "margin": final_cash - ctrl_cash
}

with open(os.path.join(project_root, "scratch", "trace_summary.json"), "w") as f:
    json.dump(trace_summary, f, indent=2)

print("\nTrace verification complete and saved to scratch/trace_summary.json")
print("=" * 80)
