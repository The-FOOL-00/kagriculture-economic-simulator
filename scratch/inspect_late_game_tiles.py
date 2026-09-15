import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

g = kagsim.Game(50003) # PET_CAFE + PET_CAFE
p0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

print("=== INSPECTING DAYS 24 TO 29 ON PET CAFE SEED 50003 ===")

for step in range(719):
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    a0 = p0.act(obs0)
    a1 = p1.act(obs1)
    
    day = step // 24
    hour = step % 24
    
    if hour == 0 and day >= 24:
        farm = obs0["farms"][0]
        priv = obs0["private"]
        tiles = farm["tiles"]
        empty = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("kind") == "EMPTY")
        plants = {}
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c = t.get("crop", "UNKNOWN")
                    plants[c] = plants.get(c, 0) + 1
        print(f"Day {day:2d} Dawn: Money ${farm['money']:,.0f} | Empty Tiles: {empty:2d} | Plants: {plants} | Shed: {priv['shed']}")
        
    g.step(a0, a1)
