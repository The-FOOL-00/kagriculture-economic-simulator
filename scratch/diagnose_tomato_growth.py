import os
import sys
BASE_DIR = os.path.abspath(".")
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from scratch.test_crop_sub_seed50007 import CropSubAgent

g = kagsim.Game(50037)
p_sub = CropSubAgent(substitute_tomato=True)
p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, 'extracted_agents', 'dmitrii_lb2800'))

step = 0
while not g.done:
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    a0 = p_sub.act(obs0)
    a1 = p_dmitrii.act(obs1)
    
    # Inspect player 0 tiles on Day 12, 16, 20, 24, 28
    if step % 24 == 0:
        day = step // 24
        tiles = obs0["farms"][0]["tiles"]
        plant_types = {}
        for r_idx, r in enumerate(tiles):
            for c_idx, t in enumerate(r):
                if isinstance(t, dict):
                    kind = t.get("kind")
                    crop = t.get("crop")
                    if crop:
                        plant_types[crop] = plant_types.get(crop, 0) + 1
        print(f"Day {day:2d} (Step {step:3d}): Plants on farm: {plant_types}")
        
    g.step(a0, a1)
    step += 1
