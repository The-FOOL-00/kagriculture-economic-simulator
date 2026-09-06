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

print("Day | Melons Alive | Avg Water Level | Weeds on Farm")
for d in range(12):
    s = d * 24
    farm = env.steps[s][1]["observation"]["farms"][1]
    melons = []
    weeds = 0
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict):
                if t.get("crop") == "MELON":
                    melons.append(t)
                elif t.get("kind") == "WEED":
                    weeds += 1
    avg_w = sum(t.get("water_level", 0) for t in melons) / len(melons) if melons else 0
    yields = [t.get("yield_units", 0) for t in melons]
    print(f"Day {d:2d} (Step {s:3d}): Melons={len(melons):2d}, AvgWater={avg_w:4.2f}, Weeds={weeds}, Yields={yields[:6]}")
