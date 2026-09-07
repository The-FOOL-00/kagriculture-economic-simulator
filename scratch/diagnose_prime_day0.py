import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.candidate_cl_aethel_prime as prime

env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
env.reset()

for s in range(48):
    obs = env.state[0].observation
    farm = obs["farms"][0]
    pvt = obs["private"]
    act = prime.agent(obs)
    
    cash = farm["money"]
    farmer_pos = farm["farmer"]
    hands = farm["hands"]
    farmer_act = act.get("farmer")
    hands_act = act.get("hands")
    mkt = act.get("market")
    
    tiles = farm["tiles"]
    plants = []
    pastures = []
    for y in range(5):
        for x in range(5):
            t = tiles[y][x]
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    plants.append((x, y, t.get("crop"), t.get("watered_today")))
                elif t.get("kind") == "PASTURE":
                    pastures.append((x, y, t.get("animal"), t.get("fed_today")))
                    
    print(f"Step {s:2d} (D{s//24} H{s%24:2d}): Cash=${cash:6.1f} Farmer={farmer_pos} Hands={len(hands)}")
    print(f"   FarmerAct={farmer_act} HandsActs={hands_act[:2] if hands_act else []}")
    if mkt:
        print(f"   Mkt={mkt}")
    print(f"   Plants({len(plants)}) Pastures({len(pastures)})={pastures}")
    print(f"   Shed={pvt.get('shed')} Seeds={pvt.get('seeds')}")
    
    env.step([act, None])
