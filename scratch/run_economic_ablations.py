"""
Comprehensive Multi-Arm Economic Ablation Study
Evaluates Arms A through I and Frozen V2 across 100 Matched Seeds (1000-1099 vs Starter).
Uses ProcessPoolExecutor for parallel simulation and computes full statistics:
Reward, Productive Actions, Movement Actions, Idle Actions, and Product Sales.
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
from scratch.build_economic_arms import (
    make_arm_a, make_arm_b, make_arm_c, make_arm_d,
    make_arm_e, make_arm_f, make_arm_g, make_arm_i,
    SHED_ACCESS, WELL_ACCESS, _dist, _quad
)

SEEDS = list(range(1000, 1100))

def get_agent_by_key(key):
    if key == "V2": return v2_agent
    elif key == "ARM_A": return make_arm_a()
    elif key == "ARM_B": return make_arm_b()
    elif key == "ARM_C": return make_arm_c()
    elif key == "ARM_D": return make_arm_d()
    elif key == "ARM_E": return make_arm_e()
    elif key == "ARM_F": return make_arm_f()
    elif key == "ARM_G": return make_arm_g()
    elif key == "ARM_I": return make_arm_i()
    raise ValueError(f"Unknown key {key}")

def eval_single_match(item):
    arm_key, arm_name, seed = item
    agent = get_agent_by_key(arm_key)
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    try:
        env.run([agent, "starter"])
        steps = env.steps
        total_steps = len(steps)
        p = 0
        
        moves = 0
        prod = 0
        idle = 0
        shed_visits = 0
        leg_lengths = []
        within_1 = 0
        total_trans = 0
        worker_last_prod = {}
        
        # Sales tracking
        units_sold = defaultdict(int)
        
        for s_idx in range(1, total_steps):
            prev_farm = steps[s_idx - 1][p]["observation"]["farms"][p]
            curr_farm = steps[s_idx][p]["observation"]["farms"][p]
            
            prev_w = [tuple(prev_farm["farmer"])] + [tuple(h) for h in prev_farm["hands"]]
            curr_w = [tuple(curr_farm["farmer"])] + [tuple(h) for h in curr_farm["hands"]]
            
            act = steps[s_idx][p].get("action") or {}
            market_orders = act.get("market") or []
            for o in market_orders:
                if o and isinstance(o, list) and o[0] == "SELL":
                    item_name = o[1]
                    qty = int(o[2]) if len(o) > 2 else 1
                    units_sold[item_name] += qty
            
            for w_idx in range(min(len(prev_w), len(curr_w))):
                p0 = prev_w[w_idx]
                p1 = curr_w[w_idx]
                
                if p0 != p1:
                    moves += 1
                    if p1 in SHED_ACCESS and p0 not in SHED_ACCESS:
                        shed_visits += 1
                else:
                    t_prev = prev_farm["tiles"][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                    t_curr = curr_farm["tiles"][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                    
                    is_prod = False
                    if t_prev != t_curr or p0 in SHED_ACCESS or p0 in WELL_ACCESS:
                        is_prod = True
                        
                    if is_prod:
                        prod += 1
                        if w_idx in worker_last_prod:
                            lp = worker_last_prod[w_idx]
                            d = _dist(lp, p0)
                            leg_lengths.append(d)
                            total_trans += 1
                            if d == 1:
                                within_1 += 1
                        worker_last_prod[w_idx] = p0
                    else:
                        idle += 1
                        
        final_reward = float(steps[-1][p].get("reward") or 0.0)
        mean_leg = float(np.mean(leg_lengths)) if leg_lengths else 0.0
        pct_1step = (within_1 / total_trans * 100.0) if total_trans else 0.0
        
        return {
            "arm": arm_name,
            "seed": seed,
            "reward": final_reward,
            "moves": moves,
            "prod": prod,
            "idle": idle,
            "shed_visits": shed_visits,
            "mean_leg": mean_leg,
            "pct_1step": pct_1step,
            "units_sold": dict(units_sold),
            "error": None
        }
    except Exception as e:
        return {
            "arm": arm_name,
            "seed": seed,
            "reward": 0.0,
            "moves": 0,
            "prod": 0,
            "idle": 0,
            "shed_visits": 0,
            "mean_leg": 0.0,
            "pct_1step": 0.0,
            "units_sold": {},
            "error": str(e)
        }

def run_ablation_suite(max_workers=10):
    ARM_CONFIGS = [
        ("V2", "V2 (Benchmark)"),
        ("ARM_A", "ARM A (Baseline)"),
        ("ARM_B", "ARM B (Cap 11 Hands)"),
        ("ARM_C", "ARM C (No Wheat Fert)"),
        ("ARM_D", "ARM D (Straw min 2)"),
        ("ARM_E", "ARM E (Cow Priority)"),
        ("ARM_F", "ARM F (JIT Feed 1.2)"),
        ("ARM_G", "ARM G (Pocket Flush)"),
        ("ARM_I", "ARM I (Synthesized)"),
    ]
    
    print("=" * 85)
    print(f"LAUNCHING 100-SEED MULTI-ARM ECONOMIC ABLATION (Seeds 1000-1099, {len(ARM_CONFIGS)} Arms)")
    print("=" * 85)
    
    tasks = []
    for arm_key, arm_name in ARM_CONFIGS:
        for s in SEEDS:
            tasks.append((arm_key, arm_name, s))
            
    print(f"Total simulations queued: {len(tasks)} (using {max_workers} processes)...")
    t0 = time.time()
    
    results_by_arm = defaultdict(list)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(eval_single_match, t) for t in tasks]
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results_by_arm[res["arm"]].append(res)
            completed += 1
            if completed % 100 == 0 or completed == len(tasks):
                elapsed = time.time() - t0
                print(f"  [{completed:4d}/{len(tasks)}] finished in {elapsed:5.1f}s ({completed/elapsed:4.1f} games/s)...")
                
    total_time = time.time() - t0
    print(f"\nCompleted {len(tasks)} games in {total_time:5.1f} seconds.")
    
    # Analyze and summarize results
    summary = {}
    print("\n" + "=" * 115)
    print("100-SEED ECONOMIC ABLATION BENCHMARK RESULTS (Seeds 1000-1099)")
    print("=" * 115)
    print(f"{'ARM / CONFIGURATION':<24} | {'REWARD (MEAN +/- STD)':<24} | {'MEDIAN ($)':<11} | {'PROD':<7} | {'MOVES':<7} | {'IDLE':<7} | {'SHED':<6} | {'1-STEP%':<7} | {'PROD/MOV'}")
    print("-" * 115)
    
    for _, arm_name in ARM_CONFIGS:
        arm_res = results_by_arm[arm_name]
        r_arr = [m["reward"] for m in arm_res if m["error"] is None]
        p_arr = [m["prod"] for m in arm_res if m["error"] is None]
        m_arr = [m["moves"] for m in arm_res if m["error"] is None]
        i_arr = [m["idle"] for m in arm_res if m["error"] is None]
        sh_arr = [m["shed_visits"] for m in arm_res if m["error"] is None]
        s1_arr = [m["pct_1step"] for m in arm_res if m["error"] is None]
        
        mean_r = float(np.mean(r_arr)) if r_arr else 0.0
        std_r = float(np.std(r_arr)) if r_arr else 0.0
        med_r = float(np.median(r_arr)) if r_arr else 0.0
        mean_p = float(np.mean(p_arr)) if p_arr else 0.0
        mean_m = float(np.mean(m_arr)) if m_arr else 0.0
        mean_i = float(np.mean(i_arr)) if i_arr else 0.0
        mean_sh = float(np.mean(sh_arr)) if sh_arr else 0.0
        mean_s1 = float(np.mean(s1_arr)) if s1_arr else 0.0
        pm_ratio = mean_p / max(1.0, mean_m)
        
        # Product sales
        straw_arr = [m["units_sold"].get("STRAWBERRY", 0) for m in arm_res]
        fert_arr = [m["units_sold"].get("FERTILIZER", 0) for m in arm_res]
        milk_arr = [m["units_sold"].get("MILK", 0) for m in arm_res]
        wool_arr = [m["units_sold"].get("WOOL", 0) for m in arm_res]
        melon_arr = [m["units_sold"].get("MELON", 0) for m in arm_res]
        
        summary[arm_name] = {
            "mean_reward": mean_r,
            "std_reward": std_r,
            "median_reward": med_r,
            "mean_prod": mean_p,
            "mean_moves": mean_m,
            "mean_idle": mean_i,
            "mean_shed": mean_sh,
            "mean_pct_1step": mean_s1,
            "prod_move_ratio": pm_ratio,
            "mean_strawberry_sold": float(np.mean(straw_arr)),
            "mean_fertilizer_sold": float(np.mean(fert_arr)),
            "mean_milk_sold": float(np.mean(milk_arr)),
            "mean_wool_sold": float(np.mean(wool_arr)),
            "mean_melon_sold": float(np.mean(melon_arr)),
        }
        
        print(f"{arm_name:<24} | ${mean_r:10,.2f} +/- ${std_r:8,.2f} | ${med_r:9,.2f} | {mean_p:7.1f} | {mean_m:7.1f} | {mean_i:7.1f} | {mean_sh:6.1f} | {mean_s1:6.1f}% | {pm_ratio:6.3f}")
        
    print("=" * 115)
    
    print("\n" + "=" * 105)
    print("PRODUCT SALES VOLUME BY ARM (MEAN UNITS SOLD ACROSS 100 SEEDS)")
    print("=" * 105)
    print(f"{'ARM':<24} | {'STRAWBERRY':<12} | {'FERTILIZER':<12} | {'MILK':<10} | {'WOOL':<10} | {'MELON':<10}")
    print("-" * 105)
    for arm_name in summary:
        s = summary[arm_name]
        print(f"{arm_name:<24} | {s['mean_strawberry_sold']:12.1f} | {s['mean_fertilizer_sold']:12.1f} | {s['mean_milk_sold']:10.1f} | {s['mean_wool_sold']:10.1f} | {s['mean_melon_sold']:10.1f}")
    print("=" * 105)
    
    with open("scratch/economic_ablation_100seeds_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nResults successfully saved to scratch/economic_ablation_100seeds_results.json")

if __name__ == "__main__":
    run_ablation_suite(max_workers=10)
