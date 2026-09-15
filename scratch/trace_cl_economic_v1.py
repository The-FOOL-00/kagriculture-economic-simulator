import sys
import json
from collections import Counter, defaultdict
from kaggle_environments import make

# Run CL-Economic-V1 on seed 1000 against starter
cfg = {"episodeSteps": 720, "seed": 1000}
env = make("kaggriculture", configuration=cfg, debug=True)

agent_path = "candidates/candidate_cl_economic_v1.py"
env.run([agent_path, "starter"])

steps = env.steps
print(f"Total steps: {len(steps)}")
final_step = steps[-1]
print(f"CL-Economic-V1 Reward: {final_step[0].reward}")
print(f"Starter Reward: {final_step[1].reward}")

# Analyze day-by-day actions for CL-Economic-V1 for Days 0-10
for day in range(11):
    day_orders = []
    plants = Counter()
    harvests = Counter()
    places = Counter()
    builds = Counter()
    waters = 0
    fertilizes = 0
    feeds = 0
    cares = 0
    drops = 0
    digs = 0
    pickups = 0
    
    start_money = None
    end_money = None
    
    for step in range(day * 24, min(len(steps), (day + 1) * 24)):
        s = steps[step]
        obs = s[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        farm = farms[0]
        m_val = farm.get("money", 0.0)
        if start_money is None:
            start_money = m_val
        end_money = m_val
        
        act = s[0].get("action", {}) or {}
        for order in act.get("market", []):
            day_orders.append(order)
            
        units = [act.get("farmer", [])] + act.get("hands", [])
        for u in units:
            if not u: continue
            op = u[0]
            if op == "PLANT": plants[u[1]] += 1
            elif op == "HARVEST": harvests["HARVEST"] += 1
            elif op == "PLACE": places[u[1] if len(u) > 1 else "ITEM"] += 1
            elif op in ("BUILD_PASTURE", "BUILD_COOP"): builds[op] += 1
            elif op == "WATER": waters += 1
            elif op == "FERTILIZE": fertilizes += 1
            elif op == "FEED": feeds += 1
            elif op == "CARE": cares += 1
            elif op == "DROP": drops += 1
            elif op == "DIG": digs += 1
            elif op == "PICKUP": pickups += 1

    buys = Counter()
    sells = Counter()
    hires = 0
    lands = 0
    for o in day_orders:
        op = o[0]
        if op == "HIRE": hires += 1
        elif op == "BUY_LAND": lands += 1
        elif op in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
            buys[(op, o[1])] += int(o[2])
        elif op == "SELL":
            sells[o[1]] += int(o[2])

    # Also count tiles on the farm at end of day
    final_day_obs = steps[min(len(steps)-1, (day + 1) * 24 - 1)][0].get("observation", {})
    f_tiles = final_day_obs.get("farms", [{}])[0].get("tiles", [])
    crop_counts = Counter()
    anim_counts = Counter()
    pasture_count = 0
    for row in f_tiles:
        for t in row:
            if isinstance(t, dict):
                if t.get("crop"): crop_counts[t["crop"]] += 1
                if t.get("animal"): anim_counts[t["animal"]] += 1
                if t.get("kind") == "PASTURE": pasture_count += 1
                
    print(f"--- DAY {day:2d} (Cash: ${start_money:.0f} -> ${end_money:.0f}) ---")
    if hires: print(f"  Hires: {hires}")
    if lands: print(f"  Buy Land: {lands}")
    if buys: print(f"  Buys: {dict(buys)}")
    if sells: print(f"  Sells: {dict(sells)}")
    if plants: print(f"  Plants: {dict(plants)}")
    if builds: print(f"  Builds: {dict(builds)}")
    if places: print(f"  Places: {dict(places)}")
    print(f"  Farm status: Crops={dict(crop_counts)}, Animals={dict(anim_counts)}, Pastures={pasture_count}")
    print(f"  Labor actions: waters={waters}, ferts={fertilizes}, feeds={feeds}, cares={cares}, harvests={harvests['HARVEST']}, drops={drops}, digs={digs}")
