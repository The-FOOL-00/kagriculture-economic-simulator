"""
PHASE 6 & 7: TOMATO TILE COUNT AND HARVEST COHORT SWEEP.
Sweeps:
- Tomato count: 10, 15, 19, 20, 25, 30
- Cohorts: 1 (synchronized), 2 (2 cohorts), 3 (3 cohorts)
Measures:
- Realized tomato harvests
- Realized tomato revenue
- Discarded tomatoes
- Wheat reserve preservation
- Final cash reward
"""
import os
import sys
import json
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from specialized_branch_agent import DemandSpecializedAgent
from spatial_production_compiler import compile_specialized_tape

def evaluate_tomato_configuration(tiles: int, cohorts: int, seed: int = 50266):
    tape = compile_specialized_tape(
        crop="TOMATO",
        tiles_count=tiles,
        cohorts=cohorts,
        workers=12,
        batch=6,
        timing=1
    )
    
    agent = DemandSpecializedAgent(
        tomato_tiles=tiles,
        tomato_cohorts=cohorts,
        tomato_custom_tape=tape,
        enable_pizza_specialist=True
    )
    
    p_opp = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    g = kagsim.Game(seed)
    
    tomatoes_sold = 0
    tomatoes_harvested = 0
    
    while not g.done:
        obs0 = g.observe(0)
        priv0 = obs0["private"]
        prev_tom = priv0["shed"].get("TOMATO", 0)
        
        a0 = agent.act(obs0)
        a1 = p_opp.act(g.observe(1))
        
        for m in a0.get("market", []):
            if m and m[0] == "SELL" and m[1] == "TOMATO":
                tomatoes_sold += m[2]
                
        g.step(a0, a1)
        
    final_cash = g.reward(0)
    opp_cash = g.reward(1)
    margin = final_cash - opp_cash
    discarded = g.observe(0)["farms"][0].get("discarded", {}).get("TOMATO", 0)
    
    return {
        "tiles": tiles,
        "cohorts": cohorts,
        "final_cash": final_cash,
        "opp_cash": opp_cash,
        "margin": margin,
        "tomatoes_sold": tomatoes_sold,
        "discarded": discarded
    }

def run_sweeps():
    print("=" * 75)
    print("PHASE 6 & 7: TOMATO COUNT AND COHORT SWEEP (SEED 50266, PIZZA+PIZZA)")
    print("=" * 75)
    print(f"{'Tiles':<6} | {'Cohorts':<8} | {'Final Cash':<14} | {'Margin vs Dmitrii':<20} | {'Tomatoes Sold':<16} | {'Discarded':<10}")
    print("-" * 75)
    
    # Baseline V2 score
    # ClosedLoopV2 achieves $140,770 on Seed 50266
    
    results = []
    for cohorts in [1, 2, 3]:
        for count in [10, 15, 19, 20, 25, 30]:
            res = evaluate_tomato_configuration(count, cohorts, seed=50266)
            results.append(res)
            print(f"{res['tiles']:<6} | {res['cohorts']:<8} | ${res['final_cash']:<13,.0f} | ${res['margin']:<+19,.0f} | {res['tomatoes_sold']:<16} | {res['discarded']:<10}")
            
    # Save results
    with open("scratch/tomato_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_sweeps()
