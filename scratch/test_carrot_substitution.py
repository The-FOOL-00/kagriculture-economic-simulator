import os
import sys

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class CarrotSubAgent(ClosedLoopAgentV2):
    """
    Substitutes secondary Wheat with Carrot on Pet Cafe worlds
    Starting on Day 18 (step 432), when Pet Cafe is active.
    Protects animal feed reserve: only substitutes wheat if shed has >= 40 wheat.
    """
    def __init__(self):
        super().__init__(jit_headroom_threshold=96)
        self.diagnostics["carrots_planted"] = 0

    def act(self, obs):
        action = super().act(obs)
        step = int(obs["step"])
        day = step // 24
        shops = obs.get("town", {}).get("unlocked_shops", [])
        
        # Only activate if PET_CAFE or FARMERS_MARKET is active
        has_carrot_shop = ("PET_CAFE" in shops) or ("FARMERS_MARKET" in shops)
        if not has_carrot_shop:
            return action
            
        # Only substitute on Days 18 to 26 (steps 432 to 647)
        if 432 <= step <= 647:
            # Check feed reserve: do not substitute wheat if shed wheat is low
            view = mod_r.FarmView(obs)
            wheat_held = view.shed.get("WHEAT", 0)
            if wheat_held >= 30:
                # 1. Substitute BUY_SEED WHEAT -> BUY_SEED CARROT
                new_market = []
                for m in action.get("market", []):
                    if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "WHEAT":
                        new_market.append(["BUY_SEED", "CARROT", m[2]])
                    else:
                        new_market.append(m)
                action["market"] = new_market
                
                # 2. Substitute PLANT WHEAT -> PLANT CARROT
                if action.get("farmer") and action["farmer"][0] == "PLANT" and len(action["farmer"]) > 1 and action["farmer"][1] == "WHEAT":
                    action["farmer"] = ["PLANT", "CARROT"]
                    self.diagnostics["carrots_planted"] += 1
                for i, h in enumerate(action.get("hands", [])):
                    if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "WHEAT":
                        action["hands"][i] = ["PLANT", "CARROT"]
                        self.diagnostics["carrots_planted"] += 1

        return action

def test_pet_cafe_seeds():
    pet_seeds = [50002, 50003, 50009, 50016, 50017, 50024, 50048, 50062, 50086]
    print("="*80)
    print("TESTING CARROT SUBSTITUTION ON PET CAFE SEEDS")
    print("="*80)

    wins = 0
    losses = 0
    margins = []
    v2_margins = []

    for s in pet_seeds:
        # Match Seat 0: CarrotSub vs Dmitrii
        p_sub = CarrotSubAgent()
        p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g0 = kagsim.Game(s)
        while not g0.done:
            g0.step(p_sub.act(g0.observe(0)), p_dmi.act(g0.observe(1)))
        sub_s0 = g0.reward(0)
        dmi_s1 = g0.reward(1)
        m0 = sub_s0 - dmi_s1
        margins.append(m0)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1

        # Match Seat 1: Dmitrii vs CarrotSub
        p_dmi0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        p_sub1 = CarrotSubAgent()
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(p_dmi0.act(g1.observe(0)), p_sub1.act(g1.observe(1)))
        dmi_s0 = g1.reward(0)
        sub_s1 = g1.reward(1)
        m1 = sub_s1 - dmi_s0
        margins.append(m1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1

        # V2 baseline on Seat 0
        p_v2 = ClosedLoopAgentV2()
        p_dmi_v2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        gv2 = kagsim.Game(s)
        while not gv2.done:
            gv2.step(p_v2.act(gv2.observe(0)), p_dmi_v2.act(gv2.observe(1)))
        v2_s0 = gv2.reward(0)
        v2_m0 = v2_s0 - gv2.reward(1)
        v2_margins.append(v2_m0)

        print(f"Seed {s:5d}: Sub S0 ${sub_s0:,.0f} vs Dmi S1 ${dmi_s1:,.0f} (M0: {m0:+,.0f}) | Sub S1 ${sub_s1:,.0f} vs Dmi S0 ${dmi_s0:,.0f} (M1: {m1:+,.0f}) | V2 M0: {v2_m0:+,.0f} (Sub-V2: {sub_s0-v2_s0:+,.0f})")

    mean_m = sum(margins) / len(margins)
    mean_v2_m = sum(v2_margins) / len(v2_margins)
    print("-" * 80)
    print(f"Total: {len(margins)} | Wins: {wins} | Losses: {losses} | Win Rate: {wins/len(margins)*100:.1f}%")
    print(f"CarrotSub Mean Margin vs Dmitrii: ${mean_m:+,.2f} | Baseline V2 Mean Margin: ${mean_v2_m:+,.2f}")

if __name__ == "__main__":
    test_pet_cafe_seeds()
