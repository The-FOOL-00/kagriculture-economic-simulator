from collections import Counter
from kaggle_environments import make

def analyze_agent(agent_path):
    cfg = {"episodeSteps": 720, "seed": 1004}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    steps = env.steps
    
    total_sales = Counter()
    total_revenue = 0.0
    total_spent = Counter()
    
    for s in steps:
        act = s[0].get("action", {}) or {}
        obs = s[0].get("observation", {})
        prices = obs.get("market", {}).get("prices", {})
        for o in act.get("market", []):
            if o[0] == "SELL":
                qty = int(o[2])
                p = float(prices.get(o[1], 100))
                total_sales[o[1]] += qty
                total_revenue += qty * p
            elif o[0] in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
                total_spent[o[1]] += int(o[2])
                
    reward = steps[-1][0].reward
    return reward, total_sales, total_revenue, total_spent

r1, s1, rev1, sp1 = analyze_agent("candidates/candidate_cl_economic_v1.py")
r2, s2, rev2, sp2 = analyze_agent("candidates/candidate_cl_economic_v2.py")

print(f"CL-Economic-V1: Reward=${r1:,.0f} | GrossRev=${rev1:,.0f}")
print(f"  Sales: {dict(s1)}")
print(f"  Spent: {dict(sp1)}")
print("-" * 60)
print(f"CL-Economic-V2: Reward=${r2:,.0f} | GrossRev=${rev2:,.0f}")
print(f"  Sales: {dict(s2)}")
print(f"  Spent: {dict(sp2)}")
print("-" * 60)
print(f"Reward Delta (V2 - V1): ${r2 - r1:+,.0f}")
print(f"Revenue Delta (V2 - V1): ${rev2 - rev1:+,.0f}")
for item in set(list(s1.keys()) + list(s2.keys())):
    print(f"  {item:12s}: V1={s1.get(item,0):4d} | V2={s2.get(item,0):4d} | Diff={s2.get(item,0)-s1.get(item,0):+4d}")
