import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 108, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

revenue_by_item = {}
spending_by_item = {}

for step in range(719):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    day = step // 24
    hour = step % 24
    
    # Record market sales
    m_orders = act0.get("market", [])
    for order in m_orders:
        if order[0] == "SELL":
            item, qty = order[1], order[2]
            revenue_by_item[item] = revenue_by_item.get(item, 0) + qty
        elif order[0] == "BUY_SEED":
            crop, qty = order[1], order[2]
            spending_by_item[f"SEED_{crop}"] = spending_by_item.get(f"SEED_{crop}", 0) + qty
        elif order[0] == "BUY_ANIMAL":
            animal, qty = order[1], order[2]
            spending_by_item[f"ANIMAL_{animal}"] = spending_by_item.get(f"ANIMAL_{animal}", 0) + qty
        elif order[0] == "BUY_PRODUCT":
            prod, qty = order[1], order[2]
            spending_by_item[f"PROD_{prod}"] = spending_by_item.get(f"PROD_{prod}", 0) + qty
            
    if step in (120, 200, 360, 500, 715):
        plants_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")
        cows_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        print(f"Step {step:3d} (D{day:2d} H{hour:2d}): Money=${farm0['money']:8.1f} | Plants={plants_cnt} | Cows={cows_cnt} | Shed={priv0['shed']} | Seeds={priv0['seeds']}")
        
    env.step([act0, act1])

print("\n=== TOTAL UNITS SOLD OVER EPISODE ===")
for k, v in sorted(revenue_by_item.items()):
    print(f"  {k}: {v} units")
    
print("\n=== TOTAL UNITS BOUGHT OVER EPISODE ===")
for k, v in sorted(spending_by_item.items()):
    print(f"  {k}: {v} units")
    
print(f"\nFinal Reward: Player 0 = ${env.steps[-1][0]['reward']:,.1f} | Player 1 (V2) = ${env.steps[-1][1]['reward']:,.1f}")
