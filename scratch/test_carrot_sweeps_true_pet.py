"""
PHASE 11 & 12: CARROT SWEEPS ON TRUE PET CAFE WORLDS (NO YARN).
Seeds tested:
50010: ['PET_CAFE', 'BRUNCH_SPOT']
50013: ['PET_CAFE', 'SMOOTHIE_SHOP']
50023: ['ICE_CREAM_SHOP', 'PET_CAFE']
50032: ['ICE_CREAM_SHOP', 'PET_CAFE']
50053: ['PET_CAFE', 'PET_CAFE']
50058: ['FARMERS_MARKET', 'PET_CAFE']
50069: ['PET_CAFE', 'PIZZA_SHOP']
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

PET_SEEDS = [50010, 50013, 50023, 50032, 50053, 50058, 50069]

def run_true_pet_sweeps():
    print("=" * 80)
    print("PHASE 11 & 12: CARROT SWEEP ON 7 TRUE PET CAFE WORLDS")
    print("=" * 80)
    
    # 1. Baseline ClosedLoopV2 vs Dmitrii on these seeds
    v2_scores = []
    dmi_scores = []
    for s in PET_SEEDS:
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
    print(f"{'Carrots':<10} | {'Workers':<8} | {'Mean Cash':<14} | {'Margin vs Dmitrii':<20} | {'Delta vs V2':<15}")
    print("-" * 80)
    
    results = []
    for count in [40, 60, 80, 93, 110, 130]:
        for w in [10, 11, 12, 13, 14]:
            tape = compile_specialized_tape(
                crop="CARROT",
                tiles_count=count,
                cohorts=3,
                workers=w,
                batch=10,
                timing=1
            )
            spec_scores = []
            for s in PET_SEEDS:
                agent = DemandSpecializedAgent(
                    carrot_tiles=count,
                    carrot_custom_tape=tape,
                    enable_carrot_specialist=True,
                    enable_pizza_specialist=False
                )
                p_d = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
                g = kagsim.Game(s)
                while not g.done:
                    g.step(agent.act(g.observe(0)), p_d.act(g.observe(1)))
                spec_scores.append(g.reward(0))
                
            mean_spec = sum(spec_scores) / len(spec_scores)
            margin = mean_spec - mean_dmi
            delta_v2 = mean_spec - mean_v2
            results.append({"carrots": count, "workers": w, "cash": mean_spec, "margin": margin, "delta_v2": delta_v2})
            print(f"{count:<10} | {w:<8} | ${mean_spec:<13,.0f} | ${margin:<+19,.0f} | ${delta_v2:<+14,.0f}")
            
    with open("scratch/true_pet_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_true_pet_sweeps()
