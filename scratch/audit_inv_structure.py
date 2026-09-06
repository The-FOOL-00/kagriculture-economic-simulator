import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})
env.reset()

for step in range(15):
    # Run V2 and inspect V2's observation
    obs = env.state[0].observation
    priv = obs["private"]
    invs = priv.get("inventories")
    shed = priv.get("shed")
    
    if step in (0, 1, 2, 5, 8, 10, 14):
        print(f"Step {step}: Inventories={invs}")
        print(f"  Shed={shed}")
        
    env.step([v2.agent, v2.agent])
