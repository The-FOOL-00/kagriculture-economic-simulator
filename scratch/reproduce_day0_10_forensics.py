import sys
import json
import numpy as np
from collections import Counter, defaultdict
from kaggle_environments import make

def run_match_and_profile(agent_path, opp_path, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, opp_path])
    steps = env.steps
    
    # Track day-by-day metrics for agent 0
    days_data = []
    for day in range(15):
        s_step = day * 24
        e_step = min(len(steps) - 1, (day + 1) * 24 - 1)
        
        obs_start = steps[s_step][0].get("observation", {})
        obs_end = steps[e_step][0].get("observation", {})
        
        farm_start = obs_start.get("farms", [{}])[0]
        farm_end = obs_end.get("farms", [{}])[0]
        priv_end = obs_end.get("private", {})
        
        cash_start = farm_start.get("money", 0.0)
        cash_end = farm_end.get("money", 0.0)
        
        # Action aggregations for this day
        plants = Counter()
        buys = Counter()
        sells = Counter()
        harvests_wheat = Counter() # yield units
        ferts_applied = 0
        
        for st in range(s_step, e_step + 1):
            act = steps[st][0].get("action", {}) or {}
            for order in act.get("market", []):
                op = order[0]
                if op in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
                    buys[(op, order[1])] += int(order[2])
                elif op == "SELL":
                    sells[order[1]] += int(order[2])
            units = [act.get("farmer", [])] + act.get("hands", [])
            for u in units:
                if not u: continue
                if u[0] == "PLANT": plants[u[1]] += 1
                elif u[0] == "FERTILIZE": ferts_applied += 1
                elif u[0] == "HARVEST":
                    # Check what was harvested
                    # (Can approximate from previous step tile)
                    pass
                    
        # Tiles at end of day
        tiles = farm_end.get("tiles", [])
        crops = Counter()
        animals = Counter()
        for row in tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("crop"): crops[t["crop"]] += 1
                    if t.get("animal"): animals[t["animal"]] += 1
                    
        days_data.append({
            "day": day,
            "cash_start": cash_start,
            "cash_end": cash_end,
            "crops": dict(crops),
            "animals": dict(animals),
            "buys": dict(buys),
            "sells": dict(sells),
            "plants": dict(plants),
            "ferts_applied": ferts_applied
        })
        
    final_reward = steps[-1][0].reward or 0.0
    return final_reward, days_data

seeds = [1000, 1001, 1002]
print(f"Comparing CL-Economic-V1 vs Frozen V2 across seeds: {seeds}")

cl_rewards = []
v2_rewards = []

cl_profiles = []
v2_profiles = []

for s in seeds:
    r_cl, p_cl = run_match_and_profile("candidates/candidate_cl_economic_v1.py", "starter", s)
    r_v2, p_v2 = run_match_and_profile("candidates/slot2_aethel_refined_v2.py", "starter", s)
    cl_rewards.append(r_cl)
    v2_rewards.append(r_v2)
    cl_profiles.append(p_cl)
    v2_profiles.append(p_v2)
    print(f"Seed {s}: CL=${r_cl:,.0f} | V2=${r_v2:,.0f} | Delta=${r_v2 - r_cl:+,.0f}")

print("\nAverage Metrics by Day (Days 0 to 14):")
print(f"{'Day':4s} | {'CL Cash':10s} | {'V2 Cash':10s} | {'CL Straw':9s} | {'V2 Straw':9s} | {'CL Sheep':9s} | {'V2 Sheep':9s} | {'CL Cow':8s} | {'V2 Cow':8s}")
print("-" * 88)

for d in range(15):
    cl_c = np.mean([p[d]["cash_end"] for p in cl_profiles])
    v2_c = np.mean([p[d]["cash_end"] for p in v2_profiles])
    
    cl_str = np.mean([p[d]["crops"].get("STRAWBERRY", 0) for p in cl_profiles])
    v2_str = np.mean([p[d]["crops"].get("STRAWBERRY", 0) for p in v2_profiles])
    
    cl_shp = np.mean([p[d]["animals"].get("SHEEP", 0) for p in cl_profiles])
    v2_shp = np.mean([p[d]["animals"].get("SHEEP", 0) for p in v2_profiles])
    
    cl_cow = np.mean([p[d]["animals"].get("COW", 0) for p in cl_profiles])
    v2_cow = np.mean([p[d]["animals"].get("COW", 0) for p in v2_profiles])
    
    print(f"{d:4d} | ${cl_c:9.0f} | ${v2_c:9.0f} | {cl_str:9.1f} | {v2_str:9.1f} | {cl_shp:9.1f} | {v2_shp:9.1f} | {cl_cow:8.1f} | {v2_cow:8.1f}")
