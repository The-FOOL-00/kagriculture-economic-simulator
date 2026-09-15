import os, sys, json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

g = kagsim.Game(50001)
p0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

for step in range(144):
    g.step(p0.act(g.observe(0)), p1.act(g.observe(1)))

obs = g.observe(0)
farm = obs["farms"][0]
tiles = farm["tiles"]

print("STEP 144 FARM GRID (10x10):")
print("   " + " ".join(f"{x:2d}" for x in range(10)))
for y in range(10):
    row_str = f"{y:2d} "
    for x in range(10):
        t = tiles[y][x]
        if t == "LOCKED":
            row_str += "  X"
        elif t is None:
            row_str += "  ."
        elif isinstance(t, dict):
            k = t.get("kind")
            if k == "PASTURE":
                a = t.get("animal", "P")
                row_str += f" {a[0]}p"
            elif k == "COOP":
                row_str += " Cp"
            elif k == "PLANT":
                c = t.get("crop", "?")
                row_str += f" {c[0]}c"
            elif k == "WEED":
                row_str += "  W"
            else:
                row_str += "  ?"
        else:
            row_str += f" {str(t)[:2]}"
    print(row_str)

print("\nFarmer:", farm["farmer"])
print("Hands:", farm["hands"])
print("Money:", farm["money"])
print("Shed:", obs["private"]["shed"])
print("Seeds:", obs["private"]["seeds"])
print("Unlocked:", farm["unlocked_quadrants"])
