"""
Check V2 wheat harvest actions.
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

cfg = {"episodeSteps": 720, "seed": 5000}
env = kaggle_environments.make("kaggriculture", configuration=cfg)
env.run([v2_agent, "starter"])
steps = env.steps

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
                if p_y >= 4 and c_y == 0:
                    act = steps[s][0].get("action") or {}
                    # find which worker is at (c, r)
                    positions = [p_farm.get("farmer")] + p_farm.get("hands", [])
                    actions = [act.get("farmer")] + act.get("hands", [])
                    acting_workers = []
                    for w_idx, (pos, w_act) in enumerate(zip(positions, actions)):
                        if pos == [c, r]:
                            acting_workers.append((w_idx, w_act))
                    print(f"Step {s:3d} at ({c},{r}): Wheat p_y={p_y} -> c_y={c_y}. Acting workers: {acting_workers}")
