import os
import sys
project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kaggle_environments import make

# Let's inspect FrozenControlSlot4 directly to see how it works vs ParametricStrategy
from agents.slot4_control_frozen_v2 import FrozenControlSlot4

ctrl = FrozenControlSlot4()
env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 50001}, debug=True)
obs = env.reset()[0].observation
act_ctrl = ctrl(obs)
print("Control Action 0:", act_ctrl)

from scratch.run_strategy_grid_search import ParametricStrategy
cand = ParametricStrategy(name="Test")
act_cand = cand(obs)
print("Cand Action 0:", act_cand)
