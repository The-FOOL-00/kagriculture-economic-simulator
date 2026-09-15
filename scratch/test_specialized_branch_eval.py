import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from specialized_branch_agent import DemandSpecializedAgent

def test_pizza_seeds():
    seeds = [50007, 50012, 50030, 50037, 50266]
    print(f"Testing {len(seeds)} Pizza seeds...")
    
    for s in seeds:
        # 1. ClosedLoopV2 vs Dmitrii
        p_v2 = ClosedLoopAgentV2()
        p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(p_v2.act(g1.observe(0)), p_dmitrii.act(g1.observe(1)))
        v2_cash = g1.reward(0)
        dmi_cash = g1.reward(1)
        
        # 2. Specialized Agent vs Dmitrii
        p_spec = DemandSpecializedAgent(enable_pizza_specialist=True)
        p_dmitrii2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g2 = kagsim.Game(s)
        while not g2.done:
            g2.step(p_spec.act(g2.observe(0)), p_dmitrii2.act(g2.observe(1)))
        spec_cash = g2.reward(0)
        dmi2_cash = g2.reward(1)
        
        print(f"Seed {s:5d}: V2=${v2_cash:,.0f} | Spec=${spec_cash:,.0f} | Dmi=${dmi_cash:,.0f} | Delta vs V2: ${spec_cash - v2_cash:+,.0f} | Margin vs Dmi: ${spec_cash - dmi2_cash:+,.0f}")

if __name__ == "__main__":
    test_pizza_seeds()
