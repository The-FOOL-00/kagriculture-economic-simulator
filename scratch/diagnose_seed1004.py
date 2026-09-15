import sys
from collections import Counter
from kaggle_environments import make

cfg = {"episodeSteps": 720, "seed": 1004}
env = make("kaggriculture", configuration=cfg, debug=True)
env.run(["candidates/candidate_cl_economic_v2.py", "starter"])

steps = env.steps
print(f"Total steps: {len(steps)}")
print(f"Final reward: {steps[-1][0].reward}")

# Check day-by-day cash, animals, feed, unwatered/unfed
for day in range(30):
    s_step = day * 24
    e_step = min(len(steps)-1, (day + 1) * 24 - 1)
    
    obs_start = steps[s_step][0].get("observation", {})
    obs_end = steps[e_step][0].get("observation", {})
    
    f_start = obs_start.get("farms", [{}])[0]
    f_end = obs_end.get("farms", [{}])[0]
    priv_end = obs_end.get("private", {})
    
    c_start = f_start.get("money", 0.0)
    c_end = f_end.get("money", 0.0)
    
    shed = priv_end.get("shed", {})
    wheat_shed = shed.get("WHEAT", 0)
    
    tiles = f_end.get("tiles", [])
    crops = Counter()
    animals = Counter()
    unfed = 0
    escaped = 0
    weeds = 0
    
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                if t.get("crop"): crops[t["crop"]] += 1
                if t.get("animal"):
                    animals[t["animal"]] += 1
                    if not t.get("fed_today"): unfed += 1
                if t.get("kind") == "WEED": weeds += 1
                
    buys = Counter()
    sells = Counter()
    for st in range(s_step, e_step + 1):
        act = steps[st][0].get("action", {}) or {}
        for o in act.get("market", []):
            if o[0] in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
                buys[(o[0], o[1])] += int(o[2])
            elif o[0] == "SELL":
                sells[o[1]] += int(o[2])
                
    quads = f_end.get("unlocked_quadrants", [])
    hired = f_end.get("hires_today", 0)
    print(f"Day {day:2d}: Cash ${c_start:.0f}->${c_end:.0f} | Quads={quads} | WheatShed={wheat_shed} | Animals={dict(animals)} | Crops={dict(crops)} | Weeds={weeds}")
    if buys: print(f"   Buys: {dict(buys)}")
    if sells: print(f"   Sells: {dict(sells)}")
