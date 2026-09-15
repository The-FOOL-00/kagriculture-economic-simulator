import sys
import os
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent
from candidates.candidate_cl_labor_minimal_v1 import ClosedLoopLaborMinimalV1

seed = 941000

for name, agent in [
    ("BaseQ50Agent", BaseQ50Agent(50)),
    ("L_MinimalAgent", L_MinimalAgent(50)),
    ("ClosedLoopLaborMinimalV1", ClosedLoopLaborMinimalV1(50))
]:
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = steps[-1][0]["reward"]
    # Check total wheat sales
    wheat_sold = sum(o[2] for st in steps for o in (st[0].get("action") or {}).get("market", []) if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT")
    print(f"{name:25s} | Reward: {rew} | Wheat Sold: {wheat_sold}")
