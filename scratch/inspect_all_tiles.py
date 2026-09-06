import sys
import os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

env = make("kaggriculture", configuration={"seed": 42, "episodeSteps": 26})
env.run([robust(v2.agent), robust(v2.agent)])
farm = env.steps[24][0]["observation"]["farms"][0]

print("Non-empty tiles in V2 at Step 24:")
for r in range(10):
    for c in range(10):
        t = farm["tiles"][r][c]
        if t:
            print(f"  ({r},{c}): {t}")
