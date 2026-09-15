import os, sys
sys.path.insert(0, "external_repos/kaggriculture-cppsim")
import kagsim

game = kagsim.Game(42)
for step in range(25):
    obs = game.observe(0)
    day, hour = obs["day"], obs["hour"]
    farm = obs["farms"][0]
    farmer_pos = farm["farmer"]
    
    act = {"farmer": ["PASS"], "hands": [], "market": []}
    if step == 0:
        act["market"] = [["BUY_SEED", "STRAWBERRY", 1], ["BUY_PRODUCT", "FERTILIZER", 10]]
    elif step == 1:
        act["farmer"] = ["PICKUP", "FERTILIZER", 10]
    elif step == 2:
        act["farmer"] = ["NORTH"]
    elif step == 3:
        act["farmer"] = ["PLANT", "STRAWBERRY"]
    elif step == 4:
        act["farmer"] = ["WATER"]
        
    game.step(act, {"farmer": ["PASS"], "hands": [], "market": []})
    new_obs = game.observe(0)
    tile = new_obs["farms"][0]["tiles"][3][4]
    inv = new_obs["private"]["inventories"][0]
    seeds = new_obs["private"]["seeds"]
    print(f"Step {step:2d} (d{day:02d} h{hour:02d}) pos={farmer_pos} act={act['farmer']} -> tile={tile} seeds={seeds} inv={inv}")
