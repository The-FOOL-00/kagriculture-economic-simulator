import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})
env.reset()

v2_sales = {}
v2_buys = {}

for step in range(719):
    obs1 = env.state[1].observation
    farm1 = obs1["farms"][1]
    priv1 = obs1["private"]
    
    act1 = v2.agent(obs1)
    
    m_orders = act1.get("market", [])
    for o in m_orders:
        if o[0] == "SELL":
            v2_sales[o[1]] = v2_sales.get(o[1], 0) + o[2]
        elif o[0] in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
            v2_buys[f"{o[0]}_{o[1]}"] = v2_buys.get(f"{o[0]}_{o[1]}", 0) + o[2]
            
    if step in (24, 120, 240, 360, 480, 600, 715):
        plants_cnt = sum(1 for row in farm1["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")
        cows_cnt = sum(1 for row in farm1["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_cnt = sum(1 for row in farm1["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        hands_cnt = len(farm1["hands"])
        print(f"V2 Step {step:3d} (D{step//24:2d}): Money=${farm1['money']:8.1f} | Hands={hands_cnt} | Plants={plants_cnt:2d} | Cows={cows_cnt:2d} | Sheep={sheep_cnt:2d} | Shed={priv1['shed']} | Seeds={priv1['seeds']}")
        
    env.step([v2.agent, v2.agent])

print("\n=== V2 TOTAL UNITS SOLD ===")
for k, v in sorted(v2_sales.items()):
    print(f"  {k}: {v} units")
    
print("\n=== V2 TOTAL UNITS BOUGHT ===")
for k, v in sorted(v2_buys.items()):
    print(f"  {k}: {v} units")

print(f"\nV2 Final Score: ${env.steps[-1][1]['reward']:,.1f}")
