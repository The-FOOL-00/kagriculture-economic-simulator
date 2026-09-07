import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import json
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

SEEDS = [101, 215, 333, 404, 555]

def profile_agent(agent_name, agent_fn):
    print(f"\n--- Profiling Agent: {agent_name} across {len(SEEDS)} seeds ---")
    
    total_metrics = {
        "final_bank": [],
        "crop_rev": [],
        "live_rev": [],
        "expenses": [],
        "melon_units": [],
        "strawberry_units": [],
        "wheat_units": [],
        "milk_units": [],
        "wool_units": [],
        "fertilizer_units": [],
        "prod_actions": [],
        "move_actions": [],
        "idle_actions": [],
        "time_series_bank": []
    }
    
    for seed in SEEDS:
        sales_by_item = {}
        purchases_by_item = {}
        hires_cost = 0.0
        land_cost = 0.0
        
        prod_count = 0
        move_count = 0
        idle_count = 0
        
        orig_process_market = kg._process_market
        
        def hooked_process_market(state, env_inner):
            orig_commit = kg._commit_unit
            orig_hire = kg._do_hire
            orig_buy_land = kg._do_buy_land
            
            farm0 = state[0].observation.farms[0]
            
            def hooked_commit(op, item, price, farm, private, market, shed_capacity=100):
                res = orig_commit(op, item, price, farm, private, market, shed_capacity)
                if res and farm is farm0:
                    if op == "SELL":
                        if item not in sales_by_item:
                            sales_by_item[item] = {"units": 0, "revenue": 0.0}
                        sales_by_item[item]["units"] += 1
                        sales_by_item[item]["revenue"] += price
                    elif op.startswith("BUY_"):
                        key = f"{op}_{item}"
                        if key not in purchases_by_item:
                            purchases_by_item[key] = {"units": 0, "cost": 0.0}
                        purchases_by_item[key]["units"] += 1
                        purchases_by_item[key]["cost"] += price
                return res
                
            def hooked_hire(farm, private, board_size, hire_mult):
                nonlocal hires_cost
                m_pre = farm["money"]
                orig_hire(farm, private, board_size, hire_mult)
                if farm is farm0:
                    hires_cost += (m_pre - farm["money"])
                    
            def hooked_buy_land(farm, board_size):
                nonlocal land_cost
                m_pre = farm["money"]
                orig_buy_land(farm, board_size)
                if farm is farm0:
                    land_cost += (m_pre - farm["money"])
                    
            kg._commit_unit = hooked_commit
            kg._do_hire = hooked_hire
            kg._do_buy_land = hooked_buy_land
            try:
                orig_process_market(state, env_inner)
            finally:
                kg._commit_unit = orig_commit
                kg._do_hire = orig_hire
                kg._do_buy_land = orig_buy_land

        kg._process_market = hooked_process_market
        
        # Intercept agent calls to count worker actions
        def wrapped_agent(obs, config=None):
            nonlocal prod_count, move_count, idle_count
            act = agent_fn(obs, config) if config else agent_fn(obs)
            # Count worker actions
            all_unit_ops = []
            f_act = act.get("farmer")
            if f_act:
                all_unit_ops.append(f_act[0] if isinstance(f_act, list) and f_act else str(f_act))
            for h_act in act.get("hands", []) or []:
                if h_act:
                    all_unit_ops.append(h_act[0] if isinstance(h_act, list) and h_act else str(h_act))
            
            for op in all_unit_ops:
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    move_count += 1
                elif op in ("PASS", "NONE", ""):
                    idle_count += 1
                else:
                    prod_count += 1
            return act

        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        try:
            env.run([wrapped_agent, "starter"])
        finally:
            kg._process_market = orig_process_market
            
        final_step = env.steps[-1]
        player_idx = 0
        reward = final_step[player_idx]["reward"]
        
        bank_curve = [step[player_idx]["observation"]["farms"][player_idx]["money"] for step in env.steps]
        
        crop_rev = sum(sales_by_item.get(item, {}).get("revenue", 0.0) for item in ["MELON", "STRAWBERRY", "WHEAT", "CARROT", "TOMATO"])
        live_rev = sum(sales_by_item.get(item, {}).get("revenue", 0.0) for item in ["MILK", "WOOL", "FERTILIZER", "EGG"])
        total_expenses = hires_cost + land_cost + sum(v["cost"] for v in purchases_by_item.values())
        
        total_metrics["final_bank"].append(reward)
        total_metrics["crop_rev"].append(crop_rev)
        total_metrics["live_rev"].append(live_rev)
        total_metrics["expenses"].append(total_expenses)
        total_metrics["melon_units"].append(sales_by_item.get("MELON", {}).get("units", 0))
        total_metrics["strawberry_units"].append(sales_by_item.get("STRAWBERRY", {}).get("units", 0))
        total_metrics["wheat_units"].append(sales_by_item.get("WHEAT", {}).get("units", 0))
        total_metrics["milk_units"].append(sales_by_item.get("MILK", {}).get("units", 0))
        total_metrics["wool_units"].append(sales_by_item.get("WOOL", {}).get("units", 0))
        total_metrics["fertilizer_units"].append(sales_by_item.get("FERTILIZER", {}).get("units", 0))
        total_metrics["prod_actions"].append(prod_count)
        total_metrics["move_actions"].append(move_count)
        total_metrics["idle_actions"].append(idle_count)
        total_metrics["time_series_bank"].append(bank_curve)
        
    summary = {}
    for k, v in total_metrics.items():
        if k == "time_series_bank":
            arr = np.array(v)
            summary[k] = list(np.mean(arr, axis=0))
        else:
            summary[k] = {
                "mean": float(np.mean(v)),
                "std": float(np.std(v)),
                "raw": v
            }
            print(f"  {k:<20}: mean={summary[k]['mean']:>12.2f}, std={summary[k]['std']:>10.2f}")
    return summary

if __name__ == "__main__":
    print("================================================================================")
    print("PHASE 2: REBUILDING V2 DETAILED ACTION PROFILE & ENGINE DECOMPOSITION")
    print("================================================================================")
    
    profiles = {
        "Frozen V2": profile_agent("Frozen V2", v2_mod.agent),
        "CL-Aethel Prime": profile_agent("CL-Aethel Prime", prime_agent),
        "CL-Aethel Grandmaster": profile_agent("CL-Aethel Grandmaster", gm_agent)
    }
    
    compact_profiles = {}
    for name, p in profiles.items():
        compact_p = {}
        for k, v in p.items():
            if k == "time_series_bank":
                ts = v
                sampled = {turn: ts[turn] for turn in range(0, 720, 24)}
                compact_p["daily_bank"] = sampled
            else:
                compact_p[k] = v
        compact_profiles[name] = compact_p
        
    with open('scratch/action_profile_decomposition.json', 'w') as f:
        json.dump(compact_profiles, f, indent=2)
    print("\nSaved detailed action profiles to scratch/action_profile_decomposition.json")
