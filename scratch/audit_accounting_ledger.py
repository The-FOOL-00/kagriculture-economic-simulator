"""
Phase 1: Candidate H vs V2 Independent Accounting Audit
Audits exact transaction ledgers across Steps 0-48 for representative seeds:
42, 100, 101, 2026, 777, 999.
"""

import sys
import os
import json

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

SEEDS = [42, 100, 101, 2026, 777, 999]

def audit_seed(seed):
    records = {"seed": seed, "V2": [], "H": []}
    
    for agent_label, agent_fn in [("V2", v2.agent), ("H", agent_H_full_jit_pipeline)]:
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        
        # Step through turns 0 to 48
        farm_history = []
        
        for step in range(49):
            obs = env.steps[-1][0]["observation"]
            money_before = obs["farms"][0]["money"]
            shed_before = dict(obs["private"]["shed"])
            prices_before = dict(obs["market"]["prices"])
            
            # Agent action
            action = agent_fn(obs)
            env.step([action, {"farmer": ["PASS"]}])
            
            obs_after = env.steps[-1][0]["observation"]
            money_after = obs_after["farms"][0]["money"]
            shed_after = dict(obs_after["private"]["shed"])
            
            # Log non-empty transactions or state changes
            market_action = action.get("market", [])
            delta_money = money_after - money_before
            
            farm_history.append({
                "step": step,
                "money_before": money_before,
                "money_after": money_after,
                "delta_money": delta_money,
                "market_orders": market_action,
                "shed_before": shed_before,
                "shed_after": shed_after,
                "prices_before": prices_before,
                "hands_count": len(obs_after["farms"][0]["hands"]),
                "hires_today": obs_after["farms"][0]["hires_today"]
            })
            
        records[agent_label] = farm_history
    return records

def analyze_accounting():
    results = {}
    for seed in SEEDS:
        records = audit_seed(seed)
        v2_s0 = records["V2"][0]
        h_s0 = records["H"][0]
        h_s1 = records["H"][1]
        
        v2_spent_s0 = -v2_s0["delta_money"]
        h_spent_s0 = -h_s0["delta_money"]
        h_spent_s1 = -h_s1["delta_money"]
        
        results[seed] = {
            "v2_money_start": v2_s0["money_before"],
            "v2_s0_spent": v2_spent_s0,
            "v2_money_end_s0": v2_s0["money_after"],
            "v2_orders_s0": v2_s0["market_orders"],
            "v2_feed_cost": v2_spent_s0 - (2 + 1200 + 500 + 560 + 100), # base non-feed orders
            "h_money_start": h_s0["money_before"],
            "h_s0_spent": h_spent_s0,
            "h_money_end_s0": h_s0["money_after"],
            "h_orders_s0": h_s0["market_orders"],
            "h_s1_spent": h_spent_s1,
            "h_orders_s1": h_s1["market_orders"],
            "step48_v2_money": records["V2"][48]["money_after"],
            "step48_h_money": records["H"][48]["money_after"],
            "step48_v2_shed": records["V2"][48]["shed_after"],
            "step48_h_shed": records["H"][48]["shed_after"]
        }
        
    print(json.dumps(results, indent=2))
    
    # Save results to json
    os.makedirs("scratch/jit_melon_results", exist_ok=True)
    with open("scratch/jit_melon_results/phase1_accounting_audit.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    analyze_accounting()
