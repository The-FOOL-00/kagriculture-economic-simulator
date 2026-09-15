import json
import os, sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54
from test_safe_liquidity_dairy import SafeDairyPolicy

def inspect_50274():
    seed = 50274
    pb = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    psafe = SafeDairyPolicy("extracted_agents/dmitrii_lb2800")
    
    gb = kagsim.Game(seed)
    gsafe = kagsim.Game(seed)
    
    while not gb.done: gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
    while not gsafe.done: gsafe.step(psafe.act(gsafe.observe(0)), v54.agent(gsafe.observe(1)))
    
    tel_b = gb.telemetry(0)
    tel_s = gsafe.telemetry(0)
    
    print(f"=== SEED 50274 COMPARISON ===")
    print(f"Base Cash: ${gb.reward(0):,.0f} | Safe Cash: ${gsafe.reward(0):,.0f} (Diff: ${gsafe.reward(0) - gb.reward(0):+,.0f})")
    print(f"Base Spend: ${tel_b.get('total_spend'):,.0f} | Sell Rev: ${tel_b.get('sell_revenue'):,.0f}")
    print(f"Safe Spend: ${tel_s.get('total_spend'):,.0f} | Sell Rev: ${tel_s.get('sell_revenue'):,.0f}")
    print(f"Base Refused: hire={tel_b.get('refused_hire')}, animal={tel_b.get('refused_buy_animal')}")
    print(f"Safe Refused: hire={tel_s.get('refused_hire')}, animal={tel_s.get('refused_buy_animal')}")
    print(f"Base Shed at End: {gb.observe(0)['private']['shed']}")
    print(f"Safe Shed at End: {gsafe.observe(0)['private']['shed']}")

if __name__ == "__main__":
    inspect_50274()
