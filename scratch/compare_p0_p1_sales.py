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
p0_sells = {}
p1_sells = {}
p0_revenue = {}
p1_revenue = {}

while not g.done:
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    a0 = p_sub.act(obs0)
    a1 = p_dmitrii.act(obs1)
    
    # Track revenue
    money0_pre = obs0["farms"][0]["money"]
    money1_pre = obs1["farms"][1]["money"]
    
    for m in a0.get('market', []):
        if m and m[0] == 'SELL':
            p0_sells[m[1]] = p0_sells.get(m[1], 0) + m[2]
    for m in a1.get('market', []):
        if m and m[0] == 'SELL':
            p1_sells[m[1]] = p1_sells.get(m[1], 0) + m[2]
            
    g.step(a0, a1)
    
    money0_post = g.reward(0)
    money1_post = g.reward(1)
    step += 1

print('P0 Sells:', p0_sells)
print('P1 Sells:', p1_sells)
print(f"P0 Final Cash: ${g.reward(0):,.0f}")
print(f"P1 Final Cash: ${g.reward(1):,.0f}")
