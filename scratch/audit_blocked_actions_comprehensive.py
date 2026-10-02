import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

seeds = [250400 + i for i in range(32)]
print(f"Auditing V49 blocked actions across {len(seeds)} seeds...")

detailed_blocks = defaultdict(int)
action_type_counts = defaultdict(int)
blocked_by_worker = defaultdict(int)
blocked_details_list = []

for s in seeds:
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset()
    for step in range(719):
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        
        # We can trace what the sim does or inspect each worker action
        farm = obs[0]["farms"][0]
        tiles = farm["tiles"]
        
        # Check farmer action
        f_act = a0.get("farmer", ["PASS"])
        fx, fy = farm["farmer"]
        action_type_counts[f_act[0]] += 1
        
        # Hands actions
        for i, h_act in enumerate(a0.get("hands", [])):
            if h_act:
                action_type_counts[h_act[0]] += 1

        obs, _, done, info = sim.step([a0, a1])
        if done:
            break

print("Total actions attempted by type:")
for k, v in sorted(action_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {k:<20}: {v:>6}")

# Now let's run instrumented engine to get exact rejection reasons from official engine
import kaggle_environments
k_env = kaggle_environments.make("kagriculture", configuration={"seed": 250416})
# Let's inspect how the official engine logs warnings or errors when actions fail
