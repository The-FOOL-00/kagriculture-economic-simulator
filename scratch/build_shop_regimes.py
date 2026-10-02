import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict
import numpy as np

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod
import kaggle_environments.envs.kaggriculture.kaggriculture as kg

seeds = [250400 + i for i in range(32)]
print(f"Sampling {len(seeds)} seeds for shop regime taxonomy and causal branch analysis...")

regime_stats = defaultdict(lambda: {"count": 0, "margins": [], "milk_demand": [], "wool_demand": [], "wheat_demand": []})

for s in seeds:
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset()
    for step in range(719):
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, _, done, _ = sim.step([a0, a1])
        if done: break
        
    m0 = float(obs[0]["farms"][0]["money"])
    m1 = float(obs[0]["farms"][1]["money"])
    margin = m0 - m1
    
    unlocked = obs[0].town.get("unlocked_shops", [])
    # Classify regime based on dominant animal/crop demand
    milk_shops = sum(1 for sh in unlocked if sh in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
    wool_shops = sum(1 for sh in unlocked if sh == "YARN_STORE")
    egg_shops = sum(1 for sh in unlocked if sh in ("BAKERY", "BRUNCH_SPOT"))
    carrot_shops = sum(1 for sh in unlocked if sh in ("PET_CAFE", "FARMERS_MARKET"))
    
    if milk_shops >= 3:
        regime = "HIGH_MILK_REGIME"
    elif wool_shops >= 2:
        regime = "HIGH_WOOL_REGIME"
    elif egg_shops >= 3:
        regime = "HIGH_EGG_REGIME"
    elif carrot_shops >= 3:
        regime = "HIGH_CARROT_REGIME"
    elif milk_shops == 0 and wool_shops == 0:
        regime = "LOW_LIVESTOCK_REGIME"
    else:
        regime = "BALANCED_MIXED_REGIME"
        
    regime_stats[regime]["count"] += 1
    regime_stats[regime]["margins"].append(margin)

print("\n--- SHOP REGIME TAXONOMY RESULTS ---")
for r, data in sorted(regime_stats.items()):
    cnt = data["count"]
    margs = data["margins"]
    avg_m = np.mean(margs) if margs else 0
    min_m = np.min(margs) if margs else 0
    max_m = np.max(margs) if margs else 0
    print(f"Regime: {r:<24} | Count: {cnt:2d} ({cnt/len(seeds)*100:4.1f}%) | Mean Margin: ${avg_m:>8.1f} | Min: ${min_m:>8.1f} | Max: ${max_m:>8.1f}")

