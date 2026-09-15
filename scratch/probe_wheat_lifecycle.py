"""
Investigate why CL-Economic-V1 harvests wheat at 1 unit yield.
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import agent as cl_agent

cfg = {"episodeSteps": 720, "seed": 5000}
env = kaggle_environments.make("kaggriculture", configuration=cfg)
env.run([cl_agent, "starter"])
steps = env.steps

print("Step-by-step history of 1-unit wheat harvests:")
for s in range(1, len(steps)):
    p_farm = steps[s-1][0]["observation"]["farms"][0]
    c_farm = steps[s][0]["observation"]["farms"][0]
    p_tiles = p_farm.get("tiles") or []
    c_tiles = c_farm.get("tiles") or []
    for r in range(len(p_tiles)):
        for c in range(len(p_tiles[r])):
            pt = p_tiles[r][c] if isinstance(p_tiles[r][c], dict) else {}
            ct = c_tiles[r][c] if isinstance(c_tiles[r][c], dict) else {}
            if pt.get("crop") == "WHEAT":
                p_y = int(pt.get("yield_units", 0) or 0)
                c_y = int(ct.get("yield_units", 0) or 0) if ct.get("crop") == "WHEAT" else 0
                if p_y > 0 and c_y < p_y and (p_y - c_y) == 1:
                    day = s // 24
                    hr = s % 24
                    p_day = pt.get("planted_day")
                    age = day - int(p_day or 0)
                    print(f"Step {s:3d} (Day {day:2d}, Hr {hr:2d}) at ({c},{r}): p_y={p_y}, c_y={c_y}, PlantedDay={p_day} (Age={age} days), Watered={pt.get('watered_today')}")
