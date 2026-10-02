import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250621)
obs = sim.reset(seed=250621)

for step in range(697):
    a0 = v49_mod.agent(obs[0])
    a1 = v44_mod.agent(obs[1])
    obs, _, done, _ = sim.step([a0, a1])

print(f"Pre-step 697 Cash: V49=${obs[0]['farms'][0]['money']}, V44=${obs[1]['farms'][1]['money']}")
print("V49 Market orders:", v49_mod.agent(obs[0]).get('market', []))
print("V44 Market orders:", v44_mod.agent(obs[1]).get('market', []))

# Let's inspect shed inventory of both before step 697
priv0 = sim.state[0].observation.private
priv1 = sim.state[1].observation.private
print("V49 shed:", priv0['shed'])
print("V44 shed:", priv1['shed'])
print("Market inventory:", obs[0]['market']['inventory'])
print("Market prices:", obs[0]['market']['prices'])
