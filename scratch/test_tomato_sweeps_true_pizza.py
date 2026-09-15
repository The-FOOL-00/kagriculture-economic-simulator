"""
PHASE 6 & 7: TOMATO SWEEP ON TRUE PIZZA WORLDS (NO YARN).
Seeds tested:
50003: ['PIZZA_SHOP', 'BRUNCH_SPOT']
50011: ['ICE_CREAM_SHOP', 'PIZZA_SHOP']
50021: ['FARMERS_MARKET', 'PIZZA_SHOP']
50026: ['PIZZA_SHOP', 'SMOOTHIE_SHOP']
50030: ['SMOOTHIE_SHOP', 'PIZZA_SHOP']
50042: ['BAKERY', 'PIZZA_SHOP']
"""
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
from spatial_production_compiler import compile_specialized_tape

PIZZA_SEEDS = [50003, 50011, 50021, 50026, 50030, 50042]

def run_true_pizza_sweeps():
    print("=" * 80)
    print("PHASE 6 & 7: TOMATO CONFIGURATION SWEEP ON 6 TRUE PIZZA WORLDS")
    print("=" * 80)
    
    # 1. Measure Baseline ClosedLoopV2 vs Dmitrii on these 6 seeds
    p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    v2_scores = []
    dmi_scores = []
    for s in PIZZA_SEEDS:
        g = kagsim.Game(s)
        p_v2 = ClosedLoopAgentV2()
        p_d = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        while not g.done:
            g.step(p_v2.act(g.observe(0)), p_d.act(g.observe(1)))
        v2_scores.append(g.reward(0))
        dmi_scores.append(g.reward(1))
        
    mean_v2 = sum(v2_scores) / len(v2_scores)
    mean_dmi = sum(dmi_scores) / len(dmi_scores)
    print(f"BASELINE CLOSED_LOOP_V2 Mean: ${mean_v2:,.0f} | DMITRII Mean: ${mean_dmi:,.0f} | Margin: ${mean_v2 - mean_dmi:+,.0f}")
    print("-" * 80)
    print(f"{'Tiles':<6} | {'Cohorts':<8} | {'Mean Cash':<14} | {'Margin vs Dmitrii':<20} | {'Delta vs V2':<15}")
    print("-" * 80)
    
    results = []
    for cohorts in [1, 2, 3]:
        for count in [10, 15, 19, 20, 25, 30]:
            tape = compile_specialized_tape(
                crop="TOMATO",
                tiles_count=count,
                cohorts=cohorts,
                workers=12,
                batch=6,
                timing=1
            )
            spec_scores = []
            for s in PIZZA_SEEDS:
                agent = DemandSpecializedAgent(
                    tomato_tiles=count,
                    tomato_cohorts=cohorts,
                    tomato_custom_tape=tape,
                    enable_pizza_specialist=True
                )
                p_d = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
                g = kagsim.Game(s)
                while not g.done:
                    g.step(agent.act(g.observe(0)), p_d.act(g.observe(1)))
                spec_scores.append(g.reward(0))
                
            mean_spec = sum(spec_scores) / len(spec_scores)
            margin = mean_spec - mean_dmi
            delta_v2 = mean_spec - mean_v2
            results.append({"tiles": count, "cohorts": cohorts, "cash": mean_spec, "margin": margin, "delta_v2": delta_v2})
            print(f"{count:<6} | {cohorts:<8} | ${mean_spec:<13,.0f} | ${margin:<+19,.0f} | ${delta_v2:<+14,.0f}")
            
    with open("scratch/true_pizza_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_true_pizza_sweeps()
