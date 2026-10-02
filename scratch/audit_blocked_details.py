import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

seeds = [250416, 250436, 250439, 250400, 250401, 250402, 250403, 250404]

# Track action opportunities
audit_records = []

for seed in seeds:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    for step in range(719):
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        
        farm = obs[0]["farms"][0]
        tiles = farm["tiles"]
        day = obs[0]["day"]
        
        # Check farmer
        f_act = a0.get("farmer", ["PASS"])
        fx, fy = farm["farmer"]
        tile = tiles[fy][fx]
        
        # Let's inspect if any action failed
        # Farmer:
        if f_act and f_act[0] == "PLANT":
            crop = f_act[1]
            if tile is not None:
                audit_records.append({
                    "seed": seed, "step": step, "unit": "farmer", "action": f_act,
                    "reason": f"tile is {tile}", "recoverable": tile == "WEED"
                })
        elif f_act and f_act[0] == "WATER":
            if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                audit_records.append({
                    "seed": seed, "step": step, "unit": "farmer", "action": f_act,
                    "reason": f"tile is {tile} (not plant)", "recoverable": False
                })
        elif f_act and f_act[0] == "HARVEST":
            if not isinstance(tile, dict) or tile.get("yield_units", 0) <= 0:
                audit_records.append({
                    "seed": seed, "step": step, "unit": "farmer", "action": f_act,
                    "reason": f"tile yield is {tile.get('yield_units', 0) if isinstance(tile, dict) else None}",
                    "recoverable": False
                })
                
        # Hands:
        for idx, h_act in enumerate(a0.get("hands", [])):
            if not h_act or idx >= len(farm["hands"]):
                continue
            hx, hy = farm["hands"][idx]
            h_tile = tiles[hy][hx]
            if h_act[0] == "PLANT":
                if h_tile is not None:
                    audit_records.append({
                        "seed": seed, "step": step, "unit": f"hand_{idx}", "action": h_act,
                        "reason": f"tile is {h_tile}", "recoverable": h_tile == "WEED"
                    })
            elif h_act[0] == "WATER":
                if not (isinstance(h_tile, dict) and h_tile.get("kind") == "PLANT"):
                    audit_records.append({
                        "seed": seed, "step": step, "unit": f"hand_{idx}", "action": h_act,
                        "reason": f"tile is {h_tile}", "recoverable": False
                    })
            elif h_act[0] == "HARVEST":
                if not isinstance(h_tile, dict) or h_tile.get("yield_units", 0) <= 0:
                    audit_records.append({
                        "seed": seed, "step": step, "unit": f"hand_{idx}", "action": h_act,
                        "reason": f"tile yield is {h_tile.get('yield_units', 0) if isinstance(h_tile, dict) else None}",
                        "recoverable": False
                    })

        obs, _, done, _ = sim.step([a0, a1])
        if done:
            break

print(f"Total audit records found: {len(audit_records)}")
reasons = defaultdict(int)
for r in audit_records:
    reasons[r["reason"]] += 1
for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:20]:
    print(f"  {k}: {v}")
