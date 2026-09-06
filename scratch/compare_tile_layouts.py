import sys
import os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

# Run V2 alone for 25 steps
env = make("kaggriculture", configuration={"seed": 42, "episodeSteps": 25})
env.run([robust(v2.agent), robust(v2.agent)])

def fmt_tile(t):
    if not t: return " . "
    if isinstance(t, str): return f"{t[:3]:>3}"
    if isinstance(t, dict):
        crop = t.get("crop")
        struct = t.get("structure")
        ttype = t.get("type", "")
        res = crop or struct or ttype or "?"
        return f"{str(res)[:3]:>3}"
    return " ? "

farm_v2 = env.steps[24][0]["observation"]["farms"][0]
print("--- V2 FARM TILES AT STEP 24 (DAY 1 START) ---")
for r_idx, row in enumerate(farm_v2["tiles"]):
    print(f"Row {r_idx:2d}: {' '.join(fmt_tile(t) for t in row)}")

# Run H alone for 25 steps
env_h = make("kaggriculture", configuration={"seed": 42, "episodeSteps": 25})
env_h.run([robust(agent_H_full_jit_pipeline), robust(v2.agent)])

farm_h = env_h.steps[24][0]["observation"]["farms"][0]
print("\n--- H FARM TILES AT STEP 24 (DAY 1 START) ---")
for r_idx, row in enumerate(farm_h["tiles"]):
    print(f"Row {r_idx:2d}: {' '.join(fmt_tile(t) for t in row)}")
