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

print("Step | FarmMelons | ShedMelons | WorkerLoads | Cash")
for s in range(255, 275):
    f1 = env.steps[s][1]["observation"]["farms"][1]
    priv1 = env.steps[s][1]["observation"]["private"]
    melons_farm = sum(1 for row in f1["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
    shed_m = priv1["shed"].get("MELON", 0)
    inventories = priv1.get("inventories", [])
    loads = [sum(inv.values()) for inv in inventories]
    cash = f1["money"]
    print(f"Step {s:3d}: FarmMelons={melons_farm:2d}, ShedMelons={shed_m:2d}, Loads={loads}, Cash={cash:8.1f}")
