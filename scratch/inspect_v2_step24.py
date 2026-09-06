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
obs = env.steps[24][0]["observation"]

print("Obs keys:", list(obs.keys()))
for k in obs:
    if k not in ("farms", "market"):
        print(f"  {k}: {obs[k]}")
if "inventories" in obs:
    print("  inventories:", obs["inventories"])
