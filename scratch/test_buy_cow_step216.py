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

print("At step 216, submitting BUY_ANIMAL COW:")
a0 = v49_mod.agent(obs[0], sim.configuration)
a0.setdefault("market", []).append(["BUY_ANIMAL", "COW", 1])
a1 = v44_mod.agent(obs[1], sim.configuration)

obs, rewards, done, info = sim.step([a0, a1])
print("Step 216 result: V49 cash =", obs[0]["farms"][0]["money"])
print("Step 216 shed:", obs[0]["private"]["shed"])
