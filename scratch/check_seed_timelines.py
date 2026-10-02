import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def check_seed_timeline(seed):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    print(f"\n=== TIMELINE FOR SEED {seed} ===")
    for step in range(350):
        if step in [72, 144, 150, 216, 288]:
            shops = obs[0]["town"]["unlocked_shops"]
            prices = obs[0]["market"]["prices"]
            opp = obs[0]["farms"][1]
            opp_cows = sum(1 for r in opp["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            opp_geese = sum(1 for r in opp["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "GOOSE")
            print(f"Step {step:3d}: Shops = {shops} | Opp = {opp_cows}C / {opp_geese}G | Milk = ${prices['MILK']}, Egg = ${prices['EGG']}")
            
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break

check_seed_timeline(250416)
check_seed_timeline(250436)
check_seed_timeline(250439)
check_seed_timeline(250428)
check_seed_timeline(250433)
check_seed_timeline(250497)
