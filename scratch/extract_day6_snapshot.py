"""
PHASE 3: EXTRACT DMITRII DAY-6 PHYSICAL SNAPSHOT (STEP 144)
Simulates Dmitrii Plan 0 up to step 144 to record the exact physical state:
worker positions, tile kinds, fences, structures, shed inventory, money.
"""
import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

def extract_snapshot(seed=50001):
    g = kagsim.Game(seed)
    p0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    for step in range(144):
        obs0 = g.observe(0)
        obs1 = g.observe(1)
        g.step(p0.act(obs0), p1.act(obs1))
        
    obs144 = g.observe(0)
    farm = obs144["farms"][0]
    priv = obs144["private"]
    
    print("=== DMITRII DAY-6 PHYSICAL SNAPSHOT (STEP 144) ===")
    print(f"Money: ${farm['money']:,.0f}")
    print(f"Total Workers: {len(farm['hands']) + 1} (Farmer at {farm['farmer']})")
    print(f"Hands positions: {farm['hands']}")
    print(f"Unlocked Quadrants: {farm['unlocked_quadrants']}")
    print(f"Shed stock: {priv['shed']}")
    
    # Analyze tiles
    coops = []
    pastures = []
    plants = {}
    empty = 0
    locked = 0
    weeds = 0
    
    for y in range(10):
        for x in range(10):
            t = farm["tiles"][y][x]
            if isinstance(t, dict):
                kind = t.get("kind")
                if kind == "COOP": coops.append((x, y))
                elif kind == "PASTURE": pastures.append((x, y))
                elif kind == "PLANT":
                    c = t.get("crop", "UNKNOWN")
                    plants[c] = plants.get(c, 0) + 1
                elif kind == "EMPTY": empty += 1
                elif kind == "LOCKED": locked += 1
                elif kind == "WEED": weeds += 1

    print(f"Coop tiles: {len(coops)} at {coops}")
    print(f"Pasture tiles: {len(pastures)} at {pastures}")
    print(f"Plants currently growing: {plants}")
    print(f"Empty tillable tiles: {empty} | Weeds: {weeds} | Locked: {locked}")

    snapshot = {
        "step": 144,
        "money": farm["money"],
        "farmer": farm["farmer"],
        "hands": farm["hands"],
        "unlocked_quadrants": farm["unlocked_quadrants"],
        "shed": priv["shed"],
        "coops": coops,
        "pastures": pastures,
        "plants": plants,
        "empty_tiles": empty
    }
    
    with open("scratch/day6_physical_snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2)
    print("Saved snapshot to scratch/day6_physical_snapshot.json")
    return snapshot

if __name__ == "__main__":
    extract_snapshot()
