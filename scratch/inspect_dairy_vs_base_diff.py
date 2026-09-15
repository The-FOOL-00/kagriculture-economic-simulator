import json
import os, sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54
from test_liquidity_guaranteed_dairy import GuaranteedPolicy

def inspect_remaining_gap(seed=50007):
    pb = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    pguard = GuaranteedPolicy("extracted_agents/dmitrii_lb2800")
    
    gb = kagsim.Game(seed)
    gg = kagsim.Game(seed)
    
    # Track items sold and money earned by item
    sales_b = {}
    sales_g = {}
    
    for s in range(719):
        ob_b = gb.observe(0)
        ob_g = gg.observe(0)
        
        act_b = pb.act(ob_b)
        act_g = pguard.act(ob_g)
        
        gb.step(act_b, v54.agent(gb.observe(1)))
        gg.step(act_g, v54.agent(gg.observe(1)))
        
    fb = gb.observe(0)["farms"][0]
    fg = gg.observe(0)["farms"][0]
    
    print(f"=== END OF GAME COMPARISON (Seed {seed}) ===")
    print(f"Base Final Cash:  ${gb.reward(0):,.0f}")
    print(f"Guard Final Cash: ${gg.reward(0):,.0f} (Gap: ${gg.reward(0) - gb.reward(0):+,.0f})")
    print(f"Base Final Shed:  {gb.observe(0)['private']['shed']}")
    print(f"Guard Final Shed: {gg.observe(0)['private']['shed']}")

if __name__ == "__main__":
    inspect_remaining_gap(50007)
    inspect_remaining_gap(50266)
