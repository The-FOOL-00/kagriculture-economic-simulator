"""
PHASE 11 & 12: PET CAFE / CARROT COMPILER & WORKER CAPACITY SWEEPS.
Tests:
- Carrot target harvest counts: 40, 60, 80, 93, 110, 130
- Worker counts: 10, 11, 12, 13, 14
- Invariant: Dedicated wheat feed tiles (>= 18 tiles) strictly preserved.
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

def evaluate_carrot_configuration(target_carrots: int, workers: int, seed: int = 50012):
    # Seed 50012 is a Pet Cafe world
    tape = compile_specialized_tape(
        crop="CARROT",
        tiles_count=target_carrots,
        cohorts=3,
        workers=workers,
        batch=10,
        timing=1
    )
    
    agent = DemandSpecializedAgent(
        carrot_tiles=target_carrots,
        carrot_custom_tape=tape,
        enable_carrot_specialist=True,
        enable_pizza_specialist=False
    )
    
    p_opp = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    g = kagsim.Game(seed)
    
    while not g.done:
        obs0 = g.observe(0)
        a0 = agent.act(obs0)
        a1 = p_opp.act(g.observe(1))
        g.step(a0, a1)
        
    final_cash = g.reward(0)
    opp_cash = g.reward(1)
    margin = final_cash - opp_cash
    
    return {
        "carrots": target_carrots,
        "workers": workers,
        "final_cash": final_cash,
        "opp_cash": opp_cash,
        "margin": margin
    }

def run_carrot_sweeps():
    print("=" * 75)
    print("PHASE 11 & 12: CARROT COUNT AND WORKER CAPACITY SWEEP (SEED 50012, PET CAFE)")
    print("=" * 75)
    print(f"{'Carrot Count':<14} | {'Workers':<8} | {'Final Cash':<14} | {'Margin vs Dmitrii':<20}")
    print("-" * 75)
    
    results = []
    for count in [40, 60, 80, 93, 110, 130]:
        for w in [10, 11, 12, 13, 14]:
            res = evaluate_carrot_configuration(count, w, seed=50012)
            results.append(res)
            print(f"{res['carrots']:<14} | {res['workers']:<8} | ${res['final_cash']:<13,.0f} | ${res['margin']:<+19,.0f}")
            
    with open("scratch/carrot_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_carrot_sweeps()
