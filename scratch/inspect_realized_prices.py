from collections import defaultdict
from kaggle_environments import make

def get_sale_prices(agent_path):
    cfg = {"episodeSteps": 720, "seed": 1004}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    steps = env.steps
    
    unit_revenues = defaultdict(float)
    unit_counts = defaultdict(int)
    
    # We can track exact money change when SELL executes
    for i in range(len(steps) - 1):
        obs_curr = steps[i][0]["observation"]
        obs_next = steps[i+1][0]["observation"]
        
        m_curr = obs_curr["farms"][0]["money"]
        m_next = obs_next["farms"][0]["money"]
        
        act = steps[i][0].get("action", {}) or {}
        market_orders = act.get("market", [])
        
        # Check market prices at current step
        prices = obs_curr.get("market", {}).get("prices", {})
        
        for o in market_orders:
            if o[0] == "SELL":
                item = o[1]
                qty = int(o[2])
                p = float(prices.get(item, 100))
                unit_revenues[item] += qty * p
                unit_counts[item] += qty
                
    return unit_revenues, unit_counts, steps[-1][0].reward

rev1, cnt1, r1 = get_sale_prices("candidates/candidate_cl_economic_v1.py")
rev2, cnt2, r2 = get_sale_prices("candidates/candidate_cl_economic_v2.py")

print(f"{'Commodity':12s} | {'V1 Count':8s} | {'V1 Price':8s} | {'V2 Count':8s} | {'V2 Price':8s} | {'Delta Rev':10s}")
print("-" * 65)

for item in ("STRAWBERRY", "MELON", "WOOL", "MILK", "FERTILIZER", "WHEAT"):
    c1 = cnt1.get(item, 0)
    p1 = rev1.get(item, 0.0) / c1 if c1 > 0 else 0.0
    c2 = cnt2.get(item, 0)
    p2 = rev2.get(item, 0.0) / c2 if c2 > 0 else 0.0
    d_rev = rev2.get(item, 0.0) - rev1.get(item, 0.0)
    print(f"{item:12s} | {c1:8d} | ${p1:7.1f} | {c2:8d} | ${p2:7.1f} | ${d_rev:+10.1f}")
