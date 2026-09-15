"""
Test Tomato substitution WITH explicit Tomato market sell orders on step % 4 == 1.
"""
import os, sys, json, copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class TomatoSpecialistV1(ClosedLoopAgentV2):
    def __init__(self, sale_batch: int = 6):
        super().__init__(jit_headroom_threshold=96)
        self.sale_batch = sale_batch
        
    def act(self, obs):
        step = int(obs["step"])
        day = step // 24
        
        # 1. On Day 11 (steps 264 to 287), substitute Strawberry -> Tomato in base tape
        action = super().act(obs)
        
        if 264 <= step <= 287:
            # Substitute seed buys
            new_m = []
            for m in action.get("market", []):
                if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "STRAWBERRY":
                    new_m.append(["BUY_SEED", "TOMATO", m[2]])
                else:
                    new_m.append(m)
            action["market"] = new_m
            
            # Substitute plants
            if action.get("farmer") and action["farmer"][0] == "PLANT" and action["farmer"][1] == "STRAWBERRY":
                action["farmer"] = ["PLANT", "TOMATO"]
            for i, h in enumerate(action.get("hands", [])):
                if h and h[0] == "PLANT" and h[1] == "STRAWBERRY":
                    action["hands"][i] = ["PLANT", "TOMATO"]
                    
        # 2. On Days 19 to 29 (steps 456 to 718):
        # Sell tomatoes on step % 4 == 1!
        if day >= 19 and step % 4 == 1:
            shed_tom = obs["private"]["shed"].get("TOMATO", 0)
            if shed_tom > 0 and len(action.get("market", [])) < 10:
                batch = min(shed_tom, self.sale_batch)
                action["market"].append(["SELL", "TOMATO", batch])
                
        # Also, replace any planned STRAWBERRY sells with TOMATO sells if we have tomatoes
        new_market = []
        for m in action.get("market", []):
            if m and m[0] == "SELL" and m[1] == "STRAWBERRY":
                shed_tom = obs["private"]["shed"].get("TOMATO", 0)
                if shed_tom > 0:
                    batch = min(shed_tom, m[2])
                    new_market.append(["SELL", "TOMATO", batch])
                else:
                    new_market.append(m)
            else:
                new_market.append(m)
        action["market"] = new_market[:10]
        
        return action

def run_test():
    seeds = [50003, 50011, 50021, 50026, 50030, 50042]
    print("=" * 80)
    print("TESTING TOMATO SPECIALIST WITH ACTIVE SALES ON 6 TRUE PIZZA WORLDS")
    print("=" * 80)
    
    for s in seeds:
        # V2 baseline
        g_v2 = kagsim.Game(s)
        p_v2 = ClosedLoopAgentV2()
        p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        while not g_v2.done:
            g_v2.step(p_v2.act(g_v2.observe(0)), p_dmi.act(g_v2.observe(1)))
        v2_cash = g_v2.reward(0)
        dmi_cash = g_v2.reward(1)
        
        # Tomato Specialist
        g_tom = kagsim.Game(s)
        p_tom = TomatoSpecialistV1(sale_batch=6)
        p_dmi2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        while not g_tom.done:
            g_tom.step(p_tom.act(g_tom.observe(0)), p_dmi2.act(g_tom.observe(1)))
        tom_cash = g_tom.reward(0)
        dmi2_cash = g_tom.reward(1)
        
        print(f"Seed {s:5d}: V2=${v2_cash:,.0f} | Tom=${tom_cash:,.0f} | Dmi=${dmi_cash:,.0f} | Delta vs V2: ${tom_cash - v2_cash:+,.0f} | Margin vs Dmi: ${tom_cash - dmi2_cash:+,.0f}")
        obs = g_tom.observe(0)
        print(f"   Tom Shed: {obs['private']['shed']} | Discarded: {obs['farms'][0].get('discarded')}")

if __name__ == "__main__":
    run_test()
