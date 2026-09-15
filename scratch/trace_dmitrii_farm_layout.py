import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import main as dmitrii_main

def inspect_farm_layout(seed=50000):
    game = kagsim.Game(seed)
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    
    # Run Dmitrii up to step 216
    dmitrii_agent = dmitrii_main.agent
    for step in range(216):
        obs = game.observe(0)
        act = dmitrii_agent(obs)
        game.step(act, idle)
        
    obs = game.observe(0)
    farm = obs["farms"][0]
    tiles = farm["tiles"]
    print("=== FARM TILES AT STEP 216 (DAY 9) ===")
    coops = []
    pastures = []
    plants = []
    weeds = []
    
    for y in range(10):
        row_str = ""
        for x in range(10):
            t = tiles[y][x]
            k = t.get("kind", "EMPTY") if isinstance(t, dict) else str(t)
            if k == "COOP":
                row_str += " C "
                coops.append((x, y))
            elif k == "PASTURE":
                row_str += " P "
                pastures.append((x, y))
            elif k == "PLANT":
                crop = t.get("crop", "P")[0]
                row_str += f" {crop} "
                plants.append((x, y, t.get("crop")))
            elif k == "WEED":
                row_str += " W "
                weeds.append((x, y))
            elif k == "LOCKED":
                row_str += " # "
            else:
                row_str += " . "
        print(row_str)
        
    print(f"\nPasture tiles ({len(pastures)}): {pastures}")
    print(f"Coop tiles ({len(coops)}): {coops}")
    print(f"Total plants ({len(plants)})")
    
    # Check animals in pastures
    private = obs["private"]
    print(f"Shed: {private['shed']}")
    print(f"Farmer pos: {farm['farmer']}")
    print(f"Hands count: {len(farm['hands'])}")
    for i, h in enumerate(farm["hands"]):
        print(f"  Hand {i+1} pos: {h}, inv: {private['inventories'][i+1]}")

if __name__ == "__main__":
    inspect_farm_layout()
