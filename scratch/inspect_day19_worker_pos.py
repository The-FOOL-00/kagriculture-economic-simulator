import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

g = kagsim.Game(50003)
p0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

for s in range(456):
    g.step(p0.act(g.observe(0)), p1.act(g.observe(1)))

print("=== WORKER POSITIONS AND ACTIONS ON DAY 19 (SEED 50003) ===")
for s in range(456, 480):
    hour = s % 24
    obs0 = g.observe(0)
    farm = obs0["farms"][0]
    farmer = farm["farmer"]
    hands = farm["hands"]
    all_pos = [farmer] + hands
    
    act0 = p0.act(obs0)
    units = [act0.get("farmer", ["PASS"])] + act0.get("hands", [])
    
    # Print workers executing HARVEST or WATER
    hw = []
    for i, u in enumerate(units):
        if u and u[0] in ["HARVEST", "WATER", "PLANT"]:
            pos = all_pos[i] if i < len(all_pos) else None
            hw.append((i, u[0], pos))
    if hw:
        print(f"Hour {hour:2d} (Step {s}): {hw}")
    g.step(act0, p1.act(g.observe(1)))
