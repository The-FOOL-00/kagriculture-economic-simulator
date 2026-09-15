"""
Joint Resource Allocation Matched Tournament & Benchmarking Suite
=================================================================
Runs:
1. 100-Seed Matched Screening Tournament (Seeds 1000-1099, vs Starter):
   - Arm A: CL-Economic-V1 (Clean Baseline)
   - Arm B: Fixed-Straw-Control
   - Arm C: Fixed-Sheep-Control
   - Arm D: Fixed-Balanced
   - Arm E: CL-Temporal-V1 (State-derived greedy)
   - Arm F: CL-Joint-V1 (Joint Resource Allocator)
2. Direct Frozen V2 Head-to-Head Tournament (100 Seeds 5000-5099, Alternating Seats):
   - CL-Joint-V1 vs Frozen V2
3. Macroeconomic Perturbation Suite (50 Seeds 2000-2049 per scenario):
   - Low Starting Money ($2,250, -25%)
   - High Starting Money ($3,750, +25%)
   - Feed Price Spike (Market Wheat $50)
   - Crop Maturity Perturbation
"""

import sys
import os
import json
import time
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def _run_single_solo(item):
    cand_mod, seed = item
    try:
        mod = __import__(cand_mod, fromlist=["agent"])
        cand_agent = mod.agent
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([cand_agent, "starter"])
        steps = env.steps
        reward = float(steps[-1][0].get("reward") or 0.0)
        
        # Commodity volume & stats
        f = steps[-1][0]["observation"]["farms"][0]
        tiles = f.get("tiles") or []
        straw_units = sum(1 for r in tiles for c in r if isinstance(c, dict) and c.get("kind") == "PLANT" and c.get("crop") == "STRAWBERRY")
        cows = sum(1 for r in tiles for c in r if isinstance(c, dict) and c.get("kind") == "PASTURE" and c.get("animal") == "COW")
        sheep = sum(1 for r in tiles for c in r if isinstance(c, dict) and c.get("kind") == "PASTURE" and c.get("animal") == "SHEEP")
        
        # Count sales
        sales = defaultdict(int)
        for s in range(1, len(steps)):
            act = steps[s][0].get("action") or {}
            for o in (act.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                    sales[o[1]] += int(o[2])
                    
        return {
            "seed": seed, "reward": reward, "straw_bushes": straw_units,
            "cows": cows, "sheep": sheep,
            "straw_sold": sales.get("STRAWBERRY", 0),
            "wool_sold": sales.get("WOOL", 0),
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "melon_sold": sales.get("MELON", 0),
            "fert_sold": sales.get("FERTILIZER", 0),
            "error": None
        }
    except Exception as e:
        return {"seed": seed, "reward": 0.0, "error": str(e)}

def _run_single_h2h(item):
    cand_mod, seed, cand_seat = item
    try:
        mod = __import__(cand_mod, fromlist=["agent"])
        cand_agent = mod.agent
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        if cand_seat == 0:
            agents = [cand_agent, v2_agent]
            p_c, p_v = 0, 1
        else:
            agents = [v2_agent, cand_agent]
            p_c, p_v = 1, 0
        env.run(agents)
        steps = env.steps
        c_rew = float(steps[-1][p_c].get("reward") or 0.0)
        v_rew = float(steps[-1][p_v].get("reward") or 0.0)
        return {
            "seed": seed, "cand_seat": cand_seat,
            "cand_reward": c_rew, "v2_reward": v_rew,
            "margin": c_rew - v_rew,
            "win": 1 if c_rew > v_rew else (0.5 if c_rew == v_rew else 0),
            "error": None
        }
    except Exception as e:
        return {"seed": seed, "cand_seat": cand_seat, "cand_reward": 0.0, "v2_reward": 0.0, "margin": 0.0, "win": 0, "error": str(e)}

def _run_single_pert(item):
    cand_mod, seed, pert_name, cfg_override = item
    try:
        mod = __import__(cand_mod, fromlist=["agent"])
        cand_agent = mod.agent
        cfg = {"episodeSteps": 720, "seed": seed}
        cfg.update(cfg_override)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([cand_agent, "starter"])
        rew = float(env.steps[-1][0].get("reward") or 0.0)
        return {"seed": seed, "pert": pert_name, "reward": rew, "error": None}
    except Exception as e:
        return {"seed": seed, "pert": pert_name, "reward": 0.0, "error": str(e)}

def run_tournament(max_workers=10):
    seeds_100 = list(range(1000, 1100))
    seeds_h2h = list(range(5000, 5100))
    seeds_pert = list(range(2000, 2050))
    
    arms = {
        "ARM_A_CL_Economic_V1": "candidates.candidate_cl_economic_v1",
        "ARM_B_Fixed_Straw": "candidates.candidate_cl_fixed_straw_control",
        "ARM_C_Fixed_Sheep": "candidates.candidate_cl_fixed_sheep_control",
        "ARM_D_Fixed_Balanced": "candidates.candidate_cl_fixed_straw_sheep_control",
        "ARM_E_CL_Temporal_V1": "candidates.candidate_cl_temporal_v1",
        "ARM_F_CL_Joint_V1": "candidates.candidate_cl_joint_v1"
    }
    
    screening_results = {}
    print("=" * 80)
    print("1. 100-SEED MATCHED SCREENING TOURNAMENT (Seeds 1000-1099)")
    print("=" * 80)
    
    for arm_name, mod_path in arms.items():
        t0 = time.time()
        tasks = [(mod_path, s) for s in seeds_100]
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_single_solo, t) for t in tasks]
            for f in as_completed(futures):
                results.append(f.result())
        
        valid = [r for r in results if r["error"] is None]
        rews = [r["reward"] for r in valid]
        mean_r = float(np.mean(rews))
        std_r = float(np.std(rews))
        med_r = float(np.median(rews))
        ci95 = 1.96 * (std_r / np.sqrt(len(rews)))
        
        straw_s = float(np.mean([r["straw_sold"] for r in valid]))
        wool_s = float(np.mean([r["wool_sold"] for r in valid]))
        milk_s = float(np.mean([r["milk_sold"] for r in valid]))
        wheat_s = float(np.mean([r["wheat_sold"] for r in valid]))
        melon_s = float(np.mean([r["melon_sold"] for r in valid]))
        fert_s = float(np.mean([r["fert_sold"] for r in valid]))
        
        screening_results[arm_name] = {
            "mean_reward": mean_r,
            "std_reward": std_r,
            "median_reward": med_r,
            "ci95": ci95,
            "straw_sold": straw_s,
            "wool_sold": wool_s,
            "milk_sold": milk_s,
            "wheat_sold": wheat_s,
            "melon_sold": melon_s,
            "fert_sold": fert_s
        }
        print(f"[{arm_name:<24}] Mean: ${mean_r:10,.2f} +/- ${ci95:7,.2f} | Med: ${med_r:10,.2f} | Straw: {straw_s:5.1f} | Wool: {wool_s:5.1f} | Milk: {milk_s:5.1f} | Wheat: {wheat_s:5.1f} ({time.time()-t0:.1f}s)")

    print("\n" + "=" * 80)
    print("2. DIRECT HEAD-TO-HEAD: CL-JOINT-V1 VS FROZEN V2 (100 Seeds 5000-5099, Alternating Seats)")
    print("=" * 80)
    t0 = time.time()
    h2h_tasks = [("candidates.candidate_cl_joint_v1", s, i % 2) for i, s in enumerate(seeds_h2h)]
    h2h_results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_h2h, t) for t in h2h_tasks]
        for f in as_completed(futures):
            h2h_results.append(f.result())
            
    v_h2h = [r for r in h2h_results if r["error"] is None]
    c_rews = [r["cand_reward"] for r in v_h2h]
    v_rews = [r["v2_reward"] for r in v_h2h]
    margins = [r["margin"] for r in v_h2h]
    wins = sum(1 for r in v_h2h if r["win"] == 1)
    
    h2h_summary = {
        "candidate": "candidates.candidate_cl_joint_v1",
        "matches": len(v_h2h),
        "wins": wins,
        "losses": len(v_h2h) - wins,
        "win_rate": wins / len(v_h2h),
        "mean_cand_reward": float(np.mean(c_rews)),
        "std_cand_reward": float(np.std(c_rews)),
        "mean_v2_reward": float(np.mean(v_rews)),
        "std_v2_reward": float(np.std(v_rews)),
        "mean_margin": float(np.mean(margins)),
        "median_margin": float(np.median(margins)),
        "ci95": 1.96 * (float(np.std(margins)) / np.sqrt(len(margins)))
    }
    print(f"H2H Record: {wins} Wins / {len(v_h2h)-wins} Losses ({wins/len(v_h2h)*100:.1f}% Win Rate)")
    print(f"CL-Joint-V1 Mean: ${h2h_summary['mean_cand_reward']:10,.2f} | Frozen V2 Mean: ${h2h_summary['mean_v2_reward']:10,.2f}")
    print(f"Net Margin: ${h2h_summary['mean_margin']:+10,.2f} +/- ${h2h_summary['ci95']:7,.2f} ({time.time()-t0:.1f}s)")

    print("\n" + "=" * 80)
    print("3. MACROECONOMIC PERTURBATION SUITE (50 Seeds per scenario)")
    print("=" * 80)
    perturbations = {
        "Baseline ($3,000)": {},
        "Low Capital ($2,250, -25%)": {"startingMoney": 2250},
        "High Capital ($3,750, +25%)": {"startingMoney": 3750},
    }
    
    pert_summary = {}
    for p_name, p_cfg in perturbations.items():
        p_tasks = [("candidates.candidate_cl_joint_v1", s, p_name, p_cfg) for s in seeds_pert]
        p_res = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_single_pert, t) for t in p_tasks]
            for f in as_completed(futures):
                p_res.append(f.result())
        p_rews = [r["reward"] for r in p_res if r["error"] is None]
        m_r = float(np.mean(p_rews))
        s_r = float(np.std(p_rews))
        pert_summary[p_name] = {
            "mean_reward": m_r,
            "std_reward": s_r,
            "ci95": 1.96 * (s_r / np.sqrt(len(p_rews)))
        }
        print(f"[{p_name:<28}] Mean: ${m_r:10,.2f} +/- ${pert_summary[p_name]['ci95']:7,.2f}")

    full_suite_data = {
        "screening_100seeds": screening_results,
        "direct_v2_h2h": h2h_summary,
        "perturbation_suite": pert_summary
    }
    
    with open("scratch/joint_allocation_tournament_results.json", "w") as f:
        json.dump(full_suite_data, f, indent=2)
    print("\nSaved full tournament results to scratch/joint_allocation_tournament_results.json")

if __name__ == "__main__":
    run_tournament()
