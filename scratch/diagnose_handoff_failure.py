import sys
import os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import CANONICAL_JIT_TRACE

def handoff_at_24(obs, config=None):
    step = obs.get("step")
    if step is None:
        step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
    else:
        step = int(step or 0)
        
    if step < 24:
        return CANONICAL_JIT_TRACE[step]
    else:
        return v2.agent(obs, config)

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

env = make("kaggriculture", configuration={"seed": 42, "episodeSteps": 35})
env.run([robust(handoff_at_24), robust(v2.agent)])

for s in range(24, 35):
    step_data = env.steps[s]
    obs0 = step_data[0]["observation"]["farms"][0]
    act0 = step_data[0].get("action", {})
    money = obs0.get("money", 0)
    wheat = obs0.get("shed", {}).get("WHEAT", 0)
    print(f"Step {s:2d}: Cash = ${money:6.1f} | Wheat in shed = {wheat:2d} | Action = {act0}")
