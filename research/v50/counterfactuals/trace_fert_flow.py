import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod

sim = FastKagricultureSim(seed=250416)
obs = sim.reset(seed=250416)
opp = load_elite_agent("V44")
agent = v49_mod.agent

for step in range(719):
    money_before = obs[0]["farms"][0]["money"]
    shed_before = obs[0]["private"]["shed"].get("FERTILIZER", 0)
    
    a = agent(obs[0])
    ao = opp.act(obs[1])
    obs, _, _, _ = sim.step([a, ao])
    
    money_after = obs[0]["farms"][0]["money"]
    shed_after = obs[0]["private"]["shed"].get("FERTILIZER", 0)
    
    d_shed = shed_after - shed_before
    d_money = money_after - money_before
    
    mkt = a.get("market", [])
    has_fert = any("FERTILIZER" in str(x) for x in mkt)
    if step >= 645 and (d_shed != 0 or has_fert):
        print(f"Step {step:03d}: d_shed={d_shed:+d} (shed={shed_after}), d_money={d_money:+0.1f}, mkt={mkt}")
