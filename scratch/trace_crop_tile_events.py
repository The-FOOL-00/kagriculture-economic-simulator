import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from scratch.test_crop_sub_seed50007 import CropSubAgent

# Run seed 50037 turn by turn and inspect farm state around day 19-30
g = kagsim.Game(50037)
p_sub = CropSubAgent(substitute_tomato=True)
p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

tomatoes_harvested = 0
strawberries_harvested = 0

step = 0
while not g.done:
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    a0 = p_sub.act(obs0)
    a1 = p_dmitrii.act(obs1)
    g.step(a0, a1)
    
    # Check end of day production
    if (step + 1) % 24 == 0:
        day = step // 24
        farm0 = g.observe(0)["farms"][0]
        farm1 = g.observe(1)["farms"][1]
        shed0 = farm0.get("shed", {})
        shed1 = farm1.get("shed", {})
        money0 = farm0.get("money", 0)
        money1 = farm1.get("money", 0)
        if day in [11, 15, 19, 21, 25, 29]:
            print(f"End of Day {day} (Step {step}):")
            print(f"  P0 (Sub): Money ${money0:,.0f} | Shed: {shed0}")
            print(f"  P1 (Dmi): Money ${money1:,.0f} | Shed: {shed1}")
            
    step += 1

print("\nFinal Result:")
print(f"P0: ${g.reward(0):,.0f} | P1: ${g.reward(1):,.0f}")
