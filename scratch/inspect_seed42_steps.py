import sys, os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
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

print("Step | Cash      | Shed Melon | Shed Wheat | Market Act")
for s in range(250, 270):
    f1 = env.steps[s][1]["observation"]["farms"][1]
    priv1 = env.steps[s][1]["observation"]["private"]
    act = env.steps[s][1].get("action", {})
    mkt = act.get("market", []) if isinstance(act, dict) else []
    print(f"{s:3d}  | {f1['money']:9.1f} | {priv1['shed'].get('MELON', 0):10d} | {priv1['shed'].get('WHEAT', 0):10d} | {mkt}")
