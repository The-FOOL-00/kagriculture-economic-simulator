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

def inspect_production_and_sales(seed=50007):
    pb = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    pguard = GuaranteedPolicy("extracted_agents/dmitrii_lb2800")
    
    gb = kagsim.Game(seed)
    gg = kagsim.Game(seed)
    
    # We can inspect telemetry from kagsim
    while not gb.done:
        gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
    while not gg.done:
        gg.step(pguard.act(gg.observe(0)), v54.agent(gg.observe(1)))
        
    tel_b = gb.telemetry(0)
    tel_g = gg.telemetry(0)
    
    print(f"=== TELEMETRY COMPARISON (Seed {seed}) ===")
    print("Base telemetry keys:", list(tel_b.keys()))
    print(f"Base Total Spend: ${tel_b.get('total_spend'):,.0f} | Sell Revenue: ${tel_b.get('sell_revenue'):,.0f}")
    print(f"Guard Total Spend: ${tel_g.get('total_spend'):,.0f} | Sell Revenue: ${tel_g.get('sell_revenue'):,.0f}")
    print("Base produced:", tel_b.get("produced"))
    print("Guard produced:", tel_g.get("produced"))
    print("Base sold units:", tel_b.get("sold_units"))
    print("Guard sold units:", tel_g.get("sold_units"))
    print(f"Base refused hire: {tel_b.get('refused_hire')} | refused buy animal: {tel_b.get('refused_buy_animal')} | refused seed: {tel_b.get('refused_seed')}")
    print(f"Guard refused hire: {tel_g.get('refused_hire')} | refused buy animal: {tel_g.get('refused_buy_animal')} | refused seed: {tel_g.get('refused_seed')}")

if __name__ == "__main__":
    inspect_production_and_sales(50007)
