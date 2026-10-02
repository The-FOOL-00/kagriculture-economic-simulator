import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod

seed = 250400
sim1 = FastKagricultureSim(seed=seed)
obs1 = sim1.reset(seed=seed)
opp1 = load_elite_agent("V44")
for step in range(719):
    a = v49_mod.agent(obs1[0])
    ao = opp1.act(obs1[1])
    obs1, _, _, _ = sim1.step([a, ao])
cash1 = obs1[0]["farms"][0]["money"]

# Now test calling v49_mod.agent ONCE per step vs TWICE per step:
sim2 = FastKagricultureSim(seed=seed)
obs2 = sim2.reset(seed=seed)
opp2 = load_elite_agent("V44")
for step in range(719):
    a = v49_mod.agent(obs2[0])
    ao = opp2.act(obs2[1])
    obs2, _, _, _ = sim2.step([a, ao])
cash2 = obs2[0]["farms"][0]["money"]

print(f"Run 1 cash: {cash1}")
print(f"Run 2 cash: {cash2}")
print(f"Parity: {cash1 == cash2}")
