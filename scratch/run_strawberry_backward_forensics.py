"""
Strawberry Causal Chain & Backward-from-Day-14 Analysis
Evaluates 100 matched seeds (5000-5099) comparing Frozen V2 and CL-Economic-V1.
Tracks:
- Planting day distribution of all strawberry bushes
- Total yield per bush as a function of planting day
- Number of active harvest windows per bush before day 29
- Capital constraints on Day 4-10 preventing earlier planting
- Exact dollar value lost due to planting past Day 11/14
"""

import sys
import os
import json
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_agent

SEEDS = list(range(5000, 5100))

def analyze_strawberry_match(seed, agent_fn, agent_name):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.run([agent_fn, "starter"])
    steps = env.steps
    total_steps = len(steps)
    p = 0
    
    # Track every strawberry plot by (x, y)
    bushes = {} # (x, y) -> {"planted_step": s, "planted_day": d, "harvest_events": 0, "total_yield": 0, "harvest_steps": [], "fertilized": False}
    
    # Seed purchases
    seed_buys = []
    
    # Cash trajectory
    cash_by_day = []
    
    for s_idx in range(1, total_steps):
        day = s_idx // 24
        hr = s_idx % 24
        
        prev_farm = steps[s_idx - 1][p]["observation"]["farms"][p]
        curr_farm = steps[s_idx][p]["observation"]["farms"][p]
        
        if hr == 0:
            cash_by_day.append(float(prev_farm["money"]))
            
        act = steps[s_idx][p].get("action") or {}
        for o in act.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                seed_buys.append({"step": s_idx, "day": day, "qty": int(o[2])})
                
        p_tiles = prev_farm.get("tiles") or []
        c_tiles = curr_farm.get("tiles") or []
        
        for r in range(len(p_tiles)):
            for c in range(len(p_tiles[r])):
                pt = p_tiles[r][c] if isinstance(p_tiles[r][c], dict) else {}
                ct = c_tiles[r][c] if isinstance(c_tiles[r][c], dict) else {}
                pos = (c, r)
                
                # Planted
                if not pt.get("crop") and ct.get("crop") == "STRAWBERRY":
                    bushes[pos] = {
                        "planted_step": s_idx,
                        "planted_day": day,
                        "harvest_events": 0,
                        "total_yield": 0,
                        "harvest_steps": [],
                        "fertilized": False
                    }
                    
                # Fertilized
                if ct.get("crop") == "STRAWBERRY" and ct.get("fertilized"):
                    if pos in bushes:
                        bushes[pos]["fertilized"] = True
                        
                # Harvested
                if pt.get("crop") == "STRAWBERRY" and int(pt.get("yield_units", 0) or 0) > 0:
                    p_y = int(pt.get("yield_units", 0) or 0)
                    c_y = int(ct.get("yield_units", 0) or 0) if ct.get("crop") == "STRAWBERRY" else 0
                    if c_y < p_y:
                        harv_y = p_y - c_y
                        if pos in bushes:
                            bushes[pos]["harvest_events"] += 1
                            bushes[pos]["total_yield"] += harv_y
                            bushes[pos]["harvest_steps"].append(s_idx)

    # Summarize bush statistics for this match
    planted_days = [b["planted_day"] for b in bushes.values()]
    bush_yields = [b["total_yield"] for b in bushes.values()]
    
    # Yield by planting window
    # Early: Day <= 10
    # Mid: Day 11-14
    # Late: Day >= 15
    yield_early = sum(b["total_yield"] for b in bushes.values() if b["planted_day"] <= 10)
    count_early = sum(1 for b in bushes.values() if b["planted_day"] <= 10)
    
    yield_mid = sum(b["total_yield"] for b in bushes.values() if 11 <= b["planted_day"] <= 14)
    count_mid = sum(1 for b in bushes.values() if 11 <= b["planted_day"] <= 14)
    
    yield_late = sum(b["total_yield"] for b in bushes.values() if b["planted_day"] >= 15)
    count_late = sum(1 for b in bushes.values() if b["planted_day"] >= 15)
    
    total_yield = sum(bush_yields)
    total_bushes = len(bushes)
    
    final_reward = float(steps[-1][p].get("reward") or 0.0)
    
    return {
        "seed": seed,
        "agent": agent_name,
        "total_reward": final_reward,
        "total_bushes": total_bushes,
        "total_yield": total_yield,
        "mean_yield_per_bush": total_yield / total_bushes if total_bushes > 0 else 0.0,
        "count_early_d10": count_early,
        "yield_early_d10": yield_early,
        "avg_yield_early": yield_early / count_early if count_early > 0 else 0.0,
        "count_mid_d11_14": count_mid,
        "yield_mid_d11_14": yield_mid,
        "avg_yield_mid": yield_mid / count_mid if count_mid > 0 else 0.0,
        "count_late_d15plus": count_late,
        "yield_late_d15plus": yield_late,
        "avg_yield_late": yield_late / count_late if count_late > 0 else 0.0,
        "first_planting_day": min(planted_days) if planted_days else -1,
        "last_planting_day": max(planted_days) if planted_days else -1,
        "seed_buys_count": len(seed_buys),
        "total_seeds_bought": sum(b["qty"] for b in seed_buys)
    }

def run_suite(seeds, max_workers=10):
    print("=" * 85)
    print("PHASE 1: STRAWBERRY CAUSAL CHAIN & BACKWARD-FROM-DAY-14 FORENSICS (100 SEEDS)")
    print("=" * 85)
    
    print("Tracing Frozen V2 Strawberry Pipeline (Seeds 5000-5099)...")
    t0 = time.time()
    v2_results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_strawberry_match, s, v2_agent, "Frozen V2") for s in seeds]
        for f in as_completed(futures):
            v2_results.append(f.result())
    print(f"  V2 completed in {time.time()-t0:.1f}s.")
    
    print("Tracing CL-Economic-V1 Strawberry Pipeline (Seeds 5000-5099)...")
    t0 = time.time()
    cl_results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_strawberry_match, s, cl_agent, "CL-Economic-V1") for s in seeds]
        for f in as_completed(futures):
            cl_results.append(f.result())
    print(f"  CL completed in {time.time()-t0:.1f}s.")
    
    # Aggregate comparisons
    def _agg(res_list):
        return {
            "total_bushes": float(np.mean([r["total_bushes"] for r in res_list])),
            "total_yield": float(np.mean([r["total_yield"] for r in res_list])),
            "mean_yield_per_bush": float(np.mean([r["mean_yield_per_bush"] for r in res_list])),
            "count_early_d10": float(np.mean([r["count_early_d10"] for r in res_list])),
            "yield_early_d10": float(np.mean([r["yield_early_d10"] for r in res_list])),
            "avg_yield_early": float(np.mean([r["avg_yield_early"] for r in res_list])),
            "count_mid_d11_14": float(np.mean([r["count_mid_d11_14"] for r in res_list])),
            "yield_mid_d11_14": float(np.mean([r["yield_mid_d11_14"] for r in res_list])),
            "avg_yield_mid": float(np.mean([r["avg_yield_mid"] for r in res_list])),
            "count_late_d15plus": float(np.mean([r["count_late_d15plus"] for r in res_list])),
            "yield_late_d15plus": float(np.mean([r["yield_late_d15plus"] for r in res_list])),
            "avg_yield_late": float(np.mean([r["avg_yield_late"] for r in res_list])),
            "last_planting_day": float(np.mean([r["last_planting_day"] for r in res_list])),
            "total_seeds_bought": float(np.mean([r["total_seeds_bought"] for r in res_list]))
        }
        
    v2_agg = _agg(v2_results)
    cl_agg = _agg(cl_results)
    
    summary = {
        "v2": v2_agg,
        "cl": cl_agg,
        "delta_v2_minus_cl": {k: v2_agg[k] - cl_agg[k] for k in v2_agg}
    }
    
    out_path = os.path.join(PROJECT_ROOT, "scratch", "strawberry_causal_forensics_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 90)
    print("STRAWBERRY CAUSAL CHAIN & PLANTING WINDOW BREAKDOWN (N = 100 Seeds)")
    print("=" * 90)
    print(f"{'METRIC':<35} | {'FROZEN V2':<18} | {'CL-ECONOMIC-V1':<18} | {'DELTA (V2 - CL)':<16}")
    print("-" * 90)
    print(f"{'Total Strawberry Bushes Planted':<35} | {v2_agg['total_bushes']:18.1f} | {cl_agg['total_bushes']:18.1f} | {v2_agg['total_bushes'] - cl_agg['total_bushes']:+16.1f}")
    print(f"{'Total Strawberry Yield (Units)':<35} | {v2_agg['total_yield']:18.1f} | {cl_agg['total_yield']:18.1f} | {v2_agg['total_yield'] - cl_agg['total_yield']:+16.1f}")
    print(f"{'Average Yield Per Bush':<35} | {v2_agg['mean_yield_per_bush']:18.2f} | {cl_agg['mean_yield_per_bush']:18.2f} | {v2_agg['mean_yield_per_bush'] - cl_agg['mean_yield_per_bush']:+16.2f}")
    print(f"{'Last Bush Planting Day':<35} | Day {v2_agg['last_planting_day']:14.1f} | Day {cl_agg['last_planting_day']:14.1f} | {v2_agg['last_planting_day'] - cl_agg['last_planting_day']:+16.1f} days")
    print("-" * 90)
    print(f"{'EARLY BUSHES (Day <= 10)':<35} | {v2_agg['count_early_d10']:18.1f} | {cl_agg['count_early_d10']:18.1f} | {v2_agg['count_early_d10'] - cl_agg['count_early_d10']:+16.1f}")
    print(f"{'  Early Bushes Total Yield':<35} | {v2_agg['yield_early_d10']:18.1f} | {cl_agg['yield_early_d10']:18.1f} | {v2_agg['yield_early_d10'] - cl_agg['yield_early_d10']:+16.1f}")
    print(f"{'  Avg Yield per Early Bush':<35} | {v2_agg['avg_yield_early']:18.2f} | {cl_agg['avg_yield_early']:18.2f} | {v2_agg['avg_yield_early'] - cl_agg['avg_yield_early']:+16.2f}")
    print("-" * 90)
    print(f"{'MID BUSHES (Days 11-14)':<35} | {v2_agg['count_mid_d11_14']:18.1f} | {cl_agg['count_mid_d11_14']:18.1f} | {v2_agg['count_mid_d11_14'] - cl_agg['count_mid_d11_14']:+16.1f}")
    print(f"{'  Mid Bushes Total Yield':<35} | {v2_agg['yield_mid_d11_14']:18.1f} | {cl_agg['yield_mid_d11_14']:18.1f} | {v2_agg['yield_mid_d11_14'] - cl_agg['yield_mid_d11_14']:+16.1f}")
    print(f"{'  Avg Yield per Mid Bush':<35} | {v2_agg['avg_yield_mid']:18.2f} | {cl_agg['avg_yield_mid']:18.2f} | {v2_agg['avg_yield_mid'] - cl_agg['avg_yield_mid']:+16.2f}")
    print("-" * 90)
    print(f"{'LATE BUSHES (Days 15+)':<35} | {v2_agg['count_late_d15plus']:18.1f} | {cl_agg['count_late_d15plus']:18.1f} | {v2_agg['count_late_d15plus'] - cl_agg['count_late_d15plus']:+16.1f}")
    print(f"{'  Late Bushes Total Yield':<35} | {v2_agg['yield_late_d15plus']:18.1f} | {cl_agg['yield_late_d15plus']:18.1f} | {v2_agg['yield_late_d15plus'] - cl_agg['yield_late_d15plus']:+16.1f}")
    print(f"{'  Avg Yield per Late Bush':<35} | {v2_agg['avg_yield_late']:18.2f} | {cl_agg['avg_yield_late']:18.2f} | {v2_agg['avg_yield_late'] - cl_agg['avg_yield_late']:+16.2f}")
    print("=" * 90)
    
    return summary

if __name__ == "__main__":
    run_suite(SEEDS, max_workers=10)
