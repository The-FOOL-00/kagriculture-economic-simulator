import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
from candidates.candidate_cl_joint_v1 import agent

cfg = {"episodeSteps": 720, "seed": 1000}
env = kaggle_environments.make("kaggriculture", configuration=cfg)
env.run([agent, "starter"])

for d in range(0, 31, 2):
    s = min(d * 24, len(env.steps) - 1)
    farm = env.steps[s][0]["observation"]["farms"][0]
    money = farm["money"]
    hands = len(farm.get("hands", []))
    tiles = farm.get("tiles", [])
    cows = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    sheep = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
    straw = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
    wheat = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "WHEAT")
    melon = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
    print(f"Day {d:2d} (step {s:3d}): Money=${money:10,.1f} | Hands={hands} | Cows={cows} Sheep={sheep} Straw={straw} Wheat={wheat} Melon={melon}")

# Look at last 5 steps
for s in range(len(env.steps) - 5, len(env.steps)):
    act = env.steps[s][0].get("action")
    print(f"Step {s}: Action={act}")
