import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250436)
obs = sim.reset()
for step in range(216):
    a0 = v49_mod.agent(obs[0], sim.configuration)
    a1 = v44_mod.agent(obs[1], sim.configuration)
    obs, _, done, _ = sim.step([a0, a1])

f0 = obs[0]["farms"][0]
print("V49 cash at Step 216:", f0["money"])
print("V49 hands at Step 216:", len(f0["hands"]))
print("V49 unlocked quadrants:", f0["unlocked_quadrants"])

# Count tiles
tile_counts = {}
for r in range(10):
    for c in range(10):
        t = f0["tiles"][r][c]
        if t is None:
            tile_counts["EMPTY"] = tile_counts.get("EMPTY", 0) + 1
        elif isinstance(t, str):
            tile_counts[t] = tile_counts.get(t, 0) + 1
        elif isinstance(t, dict):
            k = t.get("kind")
            anim = t.get("animal")
            cr = t.get("crop")
            desc = f"{k}_{anim or cr}"
            tile_counts[desc] = tile_counts.get(desc, 0) + 1

print("V49 Tile Breakdown at Step 216:")
for k, v in sorted(tile_counts.items()):
    print(f"  {k}: {v}")

# Shed contents at step 216
shed = obs[0]["private"]["shed"]
print("\nV49 Shed at Step 216:", {k: v for k, v in shed.items() if v > 0})
