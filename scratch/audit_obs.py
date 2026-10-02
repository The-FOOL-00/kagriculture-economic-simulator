import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from research.v40.env.fast_sim import FastKagricultureSim
import json

sim = FastKagricultureSim(seed=250436)
obs0, obs1 = sim.reset()

print("OBSERVATION LEVEL KEYS:")
print("obs0 keys:", [k for k in dir(obs0) if not k.startswith("_")])

# Check agent execution for 200 turns to see what tiles look like
from candidates.v49_meta_fusion.main import agent as agent49
from candidates.v44_economic_portfolio.main import agent as agent44

for step in range(160):
    a0 = agent49(obs0, sim.configuration)
    a1 = agent44(obs1, sim.configuration)
    [obs0, obs1], rewards, done, info = sim.step([a0, a1])
    if step in [0, 50, 100, 144, 150]:
        print(f"\n--- STEP {step} ---")
        f0 = obs0.farms[0]
        f1 = obs0.farms[1]
        print(f"Step {step} - P0 money: {f0['money']}, P1 money: {f1['money']}")
        print(f"P0 hands: {len(f0['hands'])}, P1 hands: {len(f1['hands'])}")
        print(f"P0 quadrants: {f0['unlocked_quadrants']}, P1 quadrants: {f1['unlocked_quadrants']}")
        
        # Let's inspect non-empty tiles for farm 1 (opponent)
        f1_tiles = {}
        for r in range(10):
            for c in range(10):
                cell = f1['tiles'][r][c]
                if cell is not None:
                    k = cell if isinstance(cell, str) else json.dumps(cell)
                    f1_tiles[k] = f1_tiles.get(k, 0) + 1
        print("P1 non-empty tiles:", f1_tiles)
        
        f0_tiles = {}
        for r in range(10):
            for c in range(10):
                cell = f0['tiles'][r][c]
                if cell is not None:
                    k = cell if isinstance(cell, str) else json.dumps(cell)
                    f0_tiles[k] = f0_tiles.get(k, 0) + 1
        print("P0 non-empty tiles:", f0_tiles)
        
        print("Market prices:", obs0.market["prices"])
        print("Market inventory:", obs0.market["inventory"])
        print("Town shops:", obs0.town["unlocked_shops"])
