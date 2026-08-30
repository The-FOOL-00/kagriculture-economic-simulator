import json
import math
from kaggle_environments import make

def trace_hybrid_execution(seed=10001):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
    
    # We will hook into step or inspect env.steps after run
    env.run(["agents/hybrid_6c3s_10m.py", "starter"])
    
    print(f"=== REPLAY ANALYSIS FOR SEED {seed} ===")
    print(f"Final Reward P0: {env.steps[-1][0].reward} | P1: {env.steps[-1][1].reward}")
    
    # Save trace data
    daily_records = []
    
    # Track day by day
    # Let's inspect env.steps structure
    # env.steps is a list of length 721 (step 0 to 720)
    # Each element is [p0_state, p1_state]
    
    for day in range(30):
        # step index for start of day
        step_idx = day * 24 + 1 # step after day start action
        step_end = min(len(env.steps) - 1, (day + 1) * 24)
        
        state_end = env.steps[step_end][0]
        obs = state_end.get("observation", {})
        farms = obs.get("farms", [])
        farm0 = farms[0] if farms else {}
        
        money = farm0.get("money", 0.0)
        tiles = farm0.get("tiles", [])
        
        # Count animals, crops, etc.
        cows = 0
        sheep = 0
        geese = 0
        pastures = 0
        coops = 0
        crop_counts = {}
        
        for row in tiles:
            for t in row:
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PASTURE":
                        pastures += 1
                        a = t.get("animal")
                        if a == "COW": cows += 1
                        elif a == "SHEEP": sheep += 1
                    elif k == "COOP":
                        coops += 1
                        a = t.get("animal")
                        if a == "GOOSE": geese += 1
                    elif k == "PLANT":
                        c = t.get("crop")
                        crop_counts[c] = crop_counts.get(c, 0) + 1
        
        # Let's also check private shed / inventory
        # Note: in kaggle_environments, private state is in obs.get("private", {})
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {})
        
        # Market prices
        market = obs.get("market", {}) or {}
        prices = market.get("prices", {})
        
        daily_records.append({
            "day": day,
            "cash": money,
            "cows": cows,
            "sheep": sheep,
            "geese": geese,
            "pastures": pastures,
            "coops": coops,
            "crops": crop_counts,
            "shed": shed,
            "prices": prices,
            "workers": 1 + len(farm0.get("hands", [])),
            "unlocked": len(farm0.get("unlocked_quadrants", []))
        })
        
    return env, daily_records

if __name__ == "__main__":
    env, daily_records = trace_hybrid_execution(10001)
    
    print("\n--- DAY 0 STEP-BY-STEP TRACE (Hours 0-23) ---")
    for h in range(24):
        s_pre = env.steps[h][0]
        s_post = env.steps[h+1][0]
        obs = s_pre.get("observation", {})
        act = s_pre.get("action", {})
        f_pre = obs.get("farms", [{}])[0]
        f_post = s_post.get("observation", {}).get("farms", [{}])[0]
        m_pre = f_pre.get("money", 0)
        m_post = f_post.get("money", 0)
        
        print(f"Step {h:2d} (Day 0, Hr {h:2d}) | Money: {m_pre:7.2f} -> {m_post:7.2f} | Act: {act}")
        
    print("\n--- DAY-BY-DAY ECONOMIC TABLE ---")
    print(f"{'Day':4} | {'Cash':9} | {'Cows':4} | {'Sheep':5} | {'Wheat':5} | {'Milk':4} | {'Wool':4} | {'Fert':4} | {'Workers':7} | {'Quads':5} | {'Crops':20}")
    for r in daily_records:
        crops_str = ", ".join(f"{k}:{v}" for k,v in r["crops"].items())
        shed = r["shed"]
        print(f"{r['day']:4d} | ${r['cash']:8.2f} | {r['cows']:4d} | {r['sheep']:5d} | {shed.get('WHEAT',0):5d} | {shed.get('MILK',0):4d} | {shed.get('WOOL',0):4d} | {shed.get('FERTILIZER',0):4d} | {r['workers']:7d} | {r['unlocked']:5d} | {crops_str:20}")
