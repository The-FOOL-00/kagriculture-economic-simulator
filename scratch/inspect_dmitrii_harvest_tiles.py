import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

g = kagsim.Game(50007)
p0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

harvests_day19 = []
harvests_day20 = []
harvests_day21 = []

for step in range(528):
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    a0 = p0.act(obs0)
    a1 = p1.act(obs1)
    
    day = step // 24
    if day in [19, 20, 21]:
        units = [a0.get("farmer", [])] + a0.get("hands", [])
        all_pos = [obs0["farms"][0]["farmer"]] + obs0["farms"][0]["hands"]
        for u_idx, u in enumerate(units):
            if u and u[0] == "HARVEST":
                pos = all_pos[u_idx] if u_idx < len(all_pos) else None
                tile = obs0["farms"][0]["tiles"][pos[1]][pos[0]] if pos else {}
                entry = (step, step % 24, u_idx, pos, tile.get("crop", "NONE"), tile.get("yield_units", 0))
                if day == 19: harvests_day19.append(entry)
                elif day == 20: harvests_day20.append(entry)
                elif day == 21: harvests_day21.append(entry)
                
    g.step(a0, a1)

print(f"Day 19 Harvests ({len(harvests_day19)}):")
for h in harvests_day19:
    print(f"  Step {h[0]} (Hr {h[1]}): Worker {h[2]} at {h[3]} -> {h[4]} (yield={h[5]})")

print(f"\nDay 20 Harvests ({len(harvests_day20)}):")
for h in harvests_day20:
    print(f"  Step {h[0]} (Hr {h[1]}): Worker {h[2]} at {h[3]} -> {h[4]} (yield={h[5]})")

print(f"\nDay 21 Harvests ({len(harvests_day21)}):")
for h in harvests_day21[:10]:
    print(f"  Step {h[0]} (Hr {h[1]}): Worker {h[2]} at {h[3]} -> {h[4]} (yield={h[5]})")
