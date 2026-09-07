import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.candidate_cl_aethel as cl
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make("kaggriculture", configuration={"seed": 42, "episodeSteps": 720})
env.reset()

for s in range(719):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    act0 = cl.agent(obs0)
    
    if s in (23, 119, 239, 263, 359, 479, 599, 711, 718):
        day = s // 24
        hour = s % 24
        melons = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
        wheat = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "WHEAT")
        straw = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
        pastures = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
        cows = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        sheep = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        unwatered = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today"))
        
        print(f"Step {s:3d} (D{day:2d} H{hour:2d}): Cash=${farm0['money']:8.1f} | Hands={len(farm0['hands'])} | Melons={melons:2d} | Wheat={wheat:2d} | Straw={straw:2d} | Pastures={pastures:2d} | Cows={cows:2d} | Sheep={sheep:2d} | Unwatered={unwatered:2d} | Shed={priv0['shed']}")
    
    act1 = v2.agent(env.state[1].observation)
    env.step([act0, act1])

print(f"\nFinal Reward P0 (CL): ${env.steps[-1][0]['reward']:,.1f} | P1 (V2): ${env.steps[-1][1]['reward']:,.1f}")
