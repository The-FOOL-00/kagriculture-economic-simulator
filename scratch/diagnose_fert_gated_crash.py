import json
import kaggle_environments
import os
import sys

sys.path.insert(0, os.getcwd())
from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

def compare_seed(seed=1004):
    print(f"=== Diagnosing Seed {seed} Divergence ===")
    env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_b = env_b.run([cl_baseline, "starter"])
    
    env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_g = env_g.run([cl_gated, "starter"])
    
    print(f"Final Money: Base=${steps_b[-1][0]['observation']['farms'][0]['money']:,} | Gated=${steps_g[-1][0]['observation']['farms'][0]['money']:,}")
    
    # Check end-of-day money progression and shed inventory
    print(f"{'Day':<4} | {'Base Money':<12} | {'Gated Money':<12} | {'Delta':<10} | {'Base Shed Fert':<14} | {'Gated Shed Fert':<15} | {'Base Shed Wheat':<15} | {'Gated Shed Wheat':<16}")
    print("-" * 110)
    for day in range(30):
        step_idx = min(len(steps_b)-1, (day + 1) * 24 - 1)
        b_obs = steps_b[step_idx][0]['observation']
        g_obs = steps_g[step_idx][0]['observation']
        
        bm = b_obs['farms'][0]['money']
        gm = g_obs['farms'][0]['money']
        
        b_shed = b_obs['private']['shed']
        g_shed = g_obs['private']['shed']
        
        b_fert = b_shed.get('FERTILIZER', 0)
        g_fert = g_shed.get('FERTILIZER', 0)
        b_wheat = b_shed.get('WHEAT', 0)
        g_wheat = g_shed.get('WHEAT', 0)
        
        print(f"{day:<4} | ${int(bm):<11,d} | ${int(gm):<11,d} | ${int(gm-bm):<+9,d} | {b_fert:<14} | {g_fert:<15} | {b_wheat:<15} | {g_wheat:<16}")

    # Check sales breakdown across the episode
    for name, steps in [("Baseline", steps_b), ("Gated", steps_g)]:
        sales = {}
        for s in steps:
            act = s[0].get("action") or {}
            for m in act.get("market", []):
                if len(m) >= 3 and m[0] == "SELL":
                    item = m[1]
                    qty = int(m[2])
                    sales[item] = sales.get(item, 0) + qty
        print(f"\n{name} Total Market Sells: {sales}")

if __name__ == "__main__":
    compare_seed(1004)
