import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    yuyajk_steps = json.load(f)["steps"]

yuyajk_trace = [s[1].get("action", {}) for s in yuyajk_steps]

def yuyajk_replay_agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    if step < len(yuyajk_trace):
        return yuyajk_trace[step]
    return {"farmer": ["PASS"], "hands": [], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 100}, debug=False)
env.run([v2.agent, yuyajk_replay_agent])

print("Step | Cash      | Melons | Market Action")
for s in range(258, 269):
    f = env.steps[s][1]["observation"]["farms"][1]
    priv = env.steps[s][1]["observation"]["private"]
    act = env.steps[s][1].get("action", {})
    mkt = act.get("market", []) if isinstance(act, dict) else []
    m_money = f.get("money", 0)
    m_melon = priv.get("shed", {}).get("MELON", 0)
    print(f"{s:3d}  | ${m_money:7.1f} | {m_melon:6d} | {mkt}")
