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

# Run V49
sim_v49 = FastKagricultureSim(seed=seed)
obs_v49 = sim_v49.reset(seed=seed)
opp_v49 = load_elite_agent("V44")
for step in range(719):
    a = v49_mod.agent(obs_v49[0])
    ao = opp_v49.act(obs_v49[1])
    if step >= 645:
        m = a.get("market", [])
        if m:
            print(f"[V49] Step {step}: money={obs_v49[0]['farms'][0]['money']}, mkt={m}")
    obs_v49, _, _, _ = sim_v49.step([a, ao])

print("\n" + "="*50 + "\n")

# Run Candidate
sim_c = FastKagricultureSim(seed=seed)
obs_c = sim_c.reset(seed=seed)
opp_c = load_elite_agent("V44")
cand = make_candidate_agent({"enable_fert_guard": True, "fert_step_threshold": 646})
for step in range(719):
    a = cand(obs_c[0])
    ao = opp_c.act(obs_c[1])
    if step >= 645:
        m = a.get("market", [])
        if m:
            print(f"[Cand] Step {step}: money={obs_c[0]['farms'][0]['money']}, mkt={m}")
    obs_c, _, _, _ = sim_c.step([a, ao])
