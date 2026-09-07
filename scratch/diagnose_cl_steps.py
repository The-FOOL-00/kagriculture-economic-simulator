import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.candidate_cl_aethel as cl
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make("kaggriculture", configuration={"seed": 42, "episodeSteps": 720})
env.reset()

for s in range(48):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    act0 = cl.agent(obs0)
    
    # Check crops & animals
    melons = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
    wheat = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "WHEAT")
    pastures = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    cows = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    
    print(f"Step {s:2d} (D{s//24:1d} H{s%24:2d}): Cash=${farm0['money']:6.1f} | Hands={len(farm0['hands'])} | Melons={melons} | Wheat={wheat} | Pastures={pastures} | Cows={cows} | FarmerAct={act0.get('farmer')} | HandsAct={act0.get('hands')[:2]} | Mkt={act0.get('market')}")
    
    env.step([act0, v2.agent(env.state[1].observation)])
