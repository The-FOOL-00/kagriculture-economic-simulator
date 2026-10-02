import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod

seed = 250428
sim = FastKagricultureSim(seed=seed)
obs = sim.reset(seed=seed)
opp = load_elite_agent("V44")
agent = v49_mod.agent

for step in range(719):
    a = agent(obs[0])
    ao = opp.act(obs[1])
    c0 = obs[0]["farms"][0]["money"]
    c1 = obs[1]["farms"][1]["money"]
    
    if step >= 680 and (step % 5 == 0 or step >= 710):
        m0 = [x for x in a.get("market", []) if x and x[0] == "SELL"]
        m1 = [x for x in ao.get("market", []) if x and x[0] == "SELL"]
        print(f"Step {step:03d}: V49 Cash={c0:.0f}, V44 Cash={c1:.0f}, Diff={c0-c1:+.0f}")
        print(f"   V49 Sells: {m0[:4]}")
        print(f"   V44 Sells: {m1[:4]}")
        
    obs, _, _, _ = sim.step([a, ao])

c0 = obs[0]["farms"][0]["money"]
c1 = obs[1]["farms"][1]["money"]
print(f"Final: V49={c0:.0f}, V44={c1:.0f}, Margin={c0-c1:+.0f}")
