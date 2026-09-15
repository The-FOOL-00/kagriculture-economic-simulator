import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

# Let's see what keys are in g.observe(0)
g = kagsim.Game(50018)
obs = g.observe(0)
print("Observation keys:", obs.keys())
if "market" in obs:
    print("Market keys:", obs["market"].keys())
