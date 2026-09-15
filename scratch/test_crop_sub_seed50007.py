import copy
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class CropSubAgent(ClosedLoopAgentV2):
    def __init__(self, substitute_tomato: bool = True, substitute_carrot: bool = True):
        super().__init__(jit_headroom_threshold=96)
        self.substitute_tomato = substitute_tomato
        self.substitute_carrot = substitute_carrot
        self.diagnostics["tomato_substitutions"] = 0
        self.diagnostics["carrot_substitutions"] = 0

    def act(self, obs):
        action = super().act(obs)
        step = int(obs["step"])
        day = step // 24
        shops = obs.get("town", {}).get("unlocked_shops", [])
        
        # Check shop conditions on Day 11 (steps 264 to 287)
        has_pizza = "PIZZA_SHOP" in shops
        has_smoothie_icecream = ("SMOOTHIE_SHOP" in shops) or ("ICE_CREAM_SHOP" in shops)
        
        # If PIZZA is present and NO Strawberry shop (Smoothie/Ice Cream) is present:
        # Substitute Day 11 Strawberry plantings with Tomato!
        if self.substitute_tomato and has_pizza and not has_smoothie_icecream:
            if 264 <= step <= 287:
                # 1. Substitute BUY_SEED in market orders
                new_market = []
                for m in action.get("market", []):
                    if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "STRAWBERRY":
                        new_market.append(["BUY_SEED", "TOMATO", m[2]])
                        self.diagnostics["tomato_substitutions"] += m[2]
                    else:
                        new_market.append(m)
                action["market"] = new_market
                
                # 2. Substitute PLANT in farmer and hands
                if action.get("farmer") and action["farmer"][0] == "PLANT" and len(action["farmer"]) > 1 and action["farmer"][1] == "STRAWBERRY":
                    action["farmer"] = ["PLANT", "TOMATO"]
                for i, h in enumerate(action.get("hands", [])):
                    if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY":
                        action["hands"][i] = ["PLANT", "TOMATO"]

        return action

def test_seed(seed: int):
    print(f"\n=================== TESTING SEED {seed} ===================")
    
    # 1. Baseline: ClosedLoopV2 vs Dmitrii
    p_cl_v2 = ClosedLoopAgentV2()
    p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    g = kagsim.Game(seed)
    while not g.done:
        g.step(p_cl_v2.act(g.observe(0)), p_dmitrii.act(g.observe(1)))
    v2_cash = g.reward(0)
    dmitrii_cash = g.reward(1)
    print(f"BASELINE V2 vs Dmitrii: V2 ${v2_cash:,.0f} vs Dmitrii ${dmitrii_cash:,.0f} (Margin: ${v2_cash - dmitrii_cash:+,.0f})")

    # 2. CropSub vs Dmitrii
    p_sub = CropSubAgent(substitute_tomato=True)
    p_dmitrii2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    g2 = kagsim.Game(seed)
    while not g2.done:
        g2.step(p_sub.act(g2.observe(0)), p_dmitrii2.act(g2.observe(1)))
    sub_cash = g2.reward(0)
    dmitrii_cash2 = g2.reward(1)
    print(f"CROP SUB vs Dmitrii:  Sub ${sub_cash:,.0f} vs Dmitrii ${dmitrii_cash2:,.0f} (Margin: ${sub_cash - dmitrii_cash2:+,.0f})")
    print(f"CROP SUB GAIN OVER V2: ${sub_cash - v2_cash:+,.0f} | Tomato substitutions: {p_sub.diagnostics['tomato_substitutions']}")

    # 3. Swap seats (Sub as Seat 1, Dmitrii as Seat 0)
    p_sub_s1 = CropSubAgent(substitute_tomato=True)
    p_dmitrii_s0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    g3 = kagsim.Game(seed)
    while not g3.done:
        g3.step(p_dmitrii_s0.act(g3.observe(0)), p_sub_s1.act(g3.observe(1)))
    dmitrii_s0_cash = g3.reward(0)
    sub_s1_cash = g3.reward(1)
    print(f"SEAT 1: Sub ${sub_s1_cash:,.0f} vs Dmitrii ${dmitrii_s0_cash:,.0f} (Margin: ${sub_s1_cash - dmitrii_s0_cash:+,.0f})")

if __name__ == "__main__":
    # Test on multiple Pizza seeds
    test_seed(50007) # PIZZA+PIZZA
    test_seed(50012) # PIZZA+PIZZA
    test_seed(50030) # BAKERY+PIZZA
    test_seed(50037) # PIZZA+PET_CAFE
