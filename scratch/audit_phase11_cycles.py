import json
import os
import sys
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

SEEDS = list(range(1000, 1050)) # 50 seeds provides ultra-tight error bars

def trace_cycles_single_match(args):
    agent_type, seed = args
    agent_fn = cl_baseline if agent_type == "Baseline" else cl_gated
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])
    
    immature_fert = 0
    mature_fert = 0
    late_fert = 0
    total_fert_actions = 0
    
    fertilized_cycles = 0
    unfertilized_cycles = 0
    total_cycles = 0
    
    # We can track production nights by observing tile yield transitions at day boundary
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx-1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}
        
        day = prev_obs["day"]
        hour = prev_obs["hour"]
        
        # Check FERTILIZE actions
        farmer_act = act.get("farmer")
        all_acts = ([farmer_act] if farmer_act else []) + [h for h in act.get("hands", []) if h]
        prev_workers = ([prev_obs["farms"][0]["farmer"]] if prev_obs["farms"][0]["farmer"] else []) + [h for h in prev_obs["farms"][0]["hands"] if h]
        
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or w_act[0] != "FERTILIZE": continue
            if w_idx >= len(prev_workers) or not prev_workers[w_idx]: continue
            wx, wy = prev_workers[w_idx]
            t = prev_obs["farms"][0]["tiles"][wy][wx]
            if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                total_fert_actions += 1
                p_day = int(t.get("planted_day", 0) or 0)
                if day <= p_day + 6:
                    immature_fert += 1
                elif day <= p_day + 15:
                    mature_fert += 1
                else:
                    late_fert += 1

        # Check production night: transition from hour 23 to hour 0 of next day
        if prev_obs["day"] != curr_obs["day"]:
            night_day = prev_obs["day"] # night of this day
            # Check every tile on farm
            for y in range(10):
                for x in range(10):
                    pt = prev_obs["farms"][0]["tiles"][y][x]
                    ct = curr_obs["farms"][0]["tiles"][y][x]
                    if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY" and isinstance(ct, dict):
                        p_day = int(pt.get("planted_day", 0) or 0)
                        # Cycles occur at end of days: p_day + 9, p_day + 11, p_day + 13, p_day + 15
                        cycles = [p_day + 9, p_day + 11, p_day + 13, p_day + 15]
                        if night_day in cycles:
                            total_cycles += 1
                            was_watered = bool(pt.get("watered_today"))
                            fert_until = int(pt.get("fertilized_until_day", -1) or -1)
                            is_fert = was_watered and (fert_until >= night_day)
                            if is_fert:
                                fertilized_cycles += 1
                            else:
                                unfertilized_cycles += 1
                                
    return {
        "agent": agent_type,
        "seed": seed,
        "total_fert_actions": total_fert_actions,
        "immature_fert": immature_fert,
        "mature_fert": mature_fert,
        "late_fert": late_fert,
        "total_cycles": total_cycles,
        "fertilized_cycles": fertilized_cycles,
        "unfertilized_cycles": unfertilized_cycles
    }

def main():
    print("Auditing Strawberry Cycle Mechanics (Seeds 1000-1049, N=50)...")
    tasks = []
    for s in SEEDS:
        tasks.append(("Baseline", s))
        tasks.append(("Gated_M1", s))
        
    results = {"Baseline": [], "Gated_M1": []}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(trace_cycles_single_match, tasks):
            results[res["agent"]].append(res)
            
    b_fert_act = np.mean([r["total_fert_actions"] for r in results["Baseline"]])
    g_fert_act = np.mean([r["total_fert_actions"] for r in results["Gated_M1"]])
    
    b_imm = np.mean([r["immature_fert"] for r in results["Baseline"]])
    g_imm = np.mean([r["immature_fert"] for r in results["Gated_M1"]])
    
    b_mat = np.mean([r["mature_fert"] for r in results["Baseline"]])
    g_mat = np.mean([r["mature_fert"] for r in results["Gated_M1"]])
    
    b_tot_cyc = np.mean([r["total_cycles"] for r in results["Baseline"]])
    g_tot_cyc = np.mean([r["total_cycles"] for r in results["Gated_M1"]])
    
    b_fert_cyc = np.mean([r["fertilized_cycles"] for r in results["Baseline"]])
    g_fert_cyc = np.mean([r["fertilized_cycles"] for r in results["Gated_M1"]])
    
    b_unfert_cyc = np.mean([r["unfertilized_cycles"] for r in results["Baseline"]])
    g_unfert_cyc = np.mean([r["unfertilized_cycles"] for r in results["Gated_M1"]])
    
    summary = {
        "b_fert_act": float(b_fert_act), "g_fert_act": float(g_fert_act), "delta_fert_act": float(g_fert_act - b_fert_act),
        "b_imm": float(b_imm), "g_imm": float(g_imm), "delta_imm": float(g_imm - b_imm),
        "b_mat": float(b_mat), "g_mat": float(g_mat), "delta_mat": float(g_mat - b_mat),
        "b_tot_cyc": float(b_tot_cyc), "g_tot_cyc": float(g_tot_cyc), "delta_tot_cyc": float(g_tot_cyc - b_tot_cyc),
        "b_fert_cyc": float(b_fert_cyc), "g_fert_cyc": float(g_fert_cyc), "delta_fert_cyc": float(g_fert_cyc - b_fert_cyc),
        "b_unfert_cyc": float(b_unfert_cyc), "g_unfert_cyc": float(g_unfert_cyc), "delta_unfert_cyc": float(g_unfert_cyc - b_unfert_cyc)
    }
    
    print("\n--- STRAWBERRY MECHANICS AUDIT RESULTS ---")
    print(f"Total Strawberry Fert Actions: Baseline = {b_fert_act:.2f}, Gated = {g_fert_act:.2f} (Delta = {g_fert_act - b_fert_act:+.2f})")
    print(f"Immature Fert Actions (D <= P+6): Baseline = {b_imm:.2f}, Gated = {g_imm:.2f} (Delta = {g_imm - b_imm:+.2f})")
    print(f"Mature Fert Actions (P+7 <= D <= P+15): Baseline = {b_mat:.2f}, Gated = {g_mat:.2f} (Delta = {g_mat - b_mat:+.2f})")
    print(f"Total Production Cycles: Baseline = {b_tot_cyc:.2f}, Gated = {g_tot_cyc:.2f} (Delta = {g_tot_cyc - b_tot_cyc:+.2f})")
    print(f"Fertilized Cycles (+2 yield): Baseline = {b_fert_cyc:.2f}, Gated = {g_fert_cyc:.2f} (Delta = {g_fert_cyc - b_fert_cyc:+.2f})")
    print(f"Unfertilized Cycles (+1 yield): Baseline = {b_unfert_cyc:.2f}, Gated = {g_unfert_cyc:.2f} (Delta = {g_unfert_cyc - b_unfert_cyc:+.2f})")
    
    with open("scratch/strawberry_mechanics_50seeds.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
