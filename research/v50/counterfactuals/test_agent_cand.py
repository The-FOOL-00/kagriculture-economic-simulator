import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from research.v50.counterfactuals.run_exact_counterfactuals import make_candidate_agent

seed = 250416
sim = FastKagricultureSim(seed=seed)
obs = sim.reset(seed=seed)
opp = load_elite_agent("V44")
agent_cand = make_candidate_agent({
    "enable_fert_guard": True,
    "fert_step_threshold": 646,
})

for step in range(719):
    a = agent_cand(obs[0])
    ao = opp.act(obs[1])
    obs, _, _, _ = sim.step([a, ao])

print("Activations:", agent_cand.activations)
print("Div step:", agent_cand.div_step)
print("Final cash cand:", obs[0]["farms"][0]["money"])
