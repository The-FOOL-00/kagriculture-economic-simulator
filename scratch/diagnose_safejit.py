import sys, os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

# Load Yuyajk trace
import json
with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    yuyajk_steps = json.load(f)["steps"]

yuyajk_trace = [s[1].get("action", {}) for s in yuyajk_steps]

def yuyajk_agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    if step < len(yuyajk_trace):
        return yuyajk_trace[step]
    return {"farmer": ["PASS"], "hands": [], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([v2.agent, yuyajk_agent])

print("=== REWARD BREAKDOWN ON SEED 42 ===")
print("V2 final reward:", env.steps[-1][0]["reward"])
print("Yuyajk final reward:", env.steps[-1][1]["reward"])

for d in range(30):
    s = d * 24
    f0 = env.steps[s][0]["observation"]["farms"][0]
    f1 = env.steps[s][1]["observation"]["farms"][1]
    m0 = f0["money"]
    m1 = f1["money"]
    print(f"Day {d:2d} (Step {s:3d}): V2 = {m0:10.1f} | Yuyajk = {m1:10.1f}")
