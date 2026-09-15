"""
Strawberry Capacity & Irrigation Experiment Runner
===================================================
Runs a controlled multi-seed evaluation across strawberry spatial & capacity variants:
- Arm A: CL-Economic-V1 (Base, Target 40, scattered)
- Arm B: Moderate Expansion (Target 24)
- Arm C: Large Expansion (Target 32)
- Arm D: Aggressive Expansion (Target 48)
- Arm E: Contiguous NE Clustered Layout (Target 36)
- Arm F: Contiguous NE + Production-Day Irrigation & Proactive Fertilization

Evaluates:
- Seeds 1000-1049 (50 matched seeds)
- Full telemetry: reward, physical commodities, watering %, movement, idle, sheds.
"""

import sys
import os
import json
import time
import copy
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments

VARIANT_MODULES = {
    "ARM_A": ("candidates.candidate_cl_economic_v1", "ClosedLoopEconomicV1", "CL-Economic-V1 (Base)"),
    "ARM_B": ("scratch.strawberry_variants", "VariantB_Moderate24", "Moderate-24"),
    "ARM_C": ("scratch.strawberry_variants", "VariantC_Large32", "Large-32"),
    "ARM_D": ("scratch.strawberry_variants", "VariantD_Aggressive48", "Aggressive-48"),
    "ARM_E": ("scratch.strawberry_variants", "VariantE_ContiguousNE", "Contiguous-NE-36"),
    "ARM_F": ("scratch.strawberry_variants", "VariantF_ActiveCare", "Contiguous-NE-ActiveCare"),
}

def _eval_single_seed(args):
    arm_id, mod_path, cls_name, seed = args
    try:
        mod = __import__(mod_path, fromlist=[cls_name])
        agent_cls = getattr(mod, cls_name)
        agent_instance = agent_cls()
        
        # Telemetry trackers
        straw_harvested = 0
        wool_harvested = 0
        milk_harvested = 0
        last_invs = None
        feed_bought = 0
        fert_collected = 0
        fert_applied = 0
        moves_count = 0
        prod_count = 0
        idle_count = 0
        daily_bush_count = defaultdict(int)
        daily_watered_count = defaultdict(int)
        shed_max = 0
        
        def tracking_agent(obs, cfg=None):
            nonlocal straw_harvested, wool_harvested, milk_harvested, last_invs
            nonlocal feed_bought, fert_collected, fert_applied, moves_count, prod_count, idle_count, shed_max
            
            step = obs["step"]
            day = obs.get("day", step // 24)
            hour = obs.get("hour", step % 24)
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            curr_shed_load = sum(shed.values())
            if curr_shed_load > shed_max:
                shed_max = curr_shed_load
                
            curr_invs = copy.deepcopy(priv.get("inventories") or [])
            if last_invs is not None:
                for ci, li in zip(curr_invs, last_invs):
                    ds = ci.get("STRAWBERRY", 0) - li.get("STRAWBERRY", 0)
                    if ds > 0: straw_harvested += ds
                    dw = ci.get("WOOL", 0) - li.get("WOOL", 0)
                    if dw > 0: wool_harvested += dw
                    dm = ci.get("MILK", 0) - li.get("MILK", 0)
                    if dm > 0: milk_harvested += dm
            last_invs = curr_invs
            
            # Count daily bush watering at hour 23
            if hour == 23:
                farm = obs["farms"][0]
                tiles = farm.get("tiles") or []
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                            daily_bush_count[day] += 1
                            if t.get("watered_today"):
                                daily_watered_count[day] += 1
            
            action = agent_instance(obs, cfg)
            
            # Tally action commands
            all_w_acts = [action.get("farmer")] + (action.get("hands") or [])
            for a in all_w_acts:
                if isinstance(a, list) and len(a) > 0:
                    cmd = a[0]
                    if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                        moves_count += 1
                    elif cmd == "PASS":
                        idle_count += 1
                    else:
                        prod_count += 1
                        if cmd == "COLLECT_FERTILIZER": fert_collected += 1
                        elif cmd == "FERTILIZE": fert_applied += 1
            
            for m in (action.get("market") or []):
                if isinstance(m, list) and len(m) > 2 and m[0] == "BUY_PRODUCT" and m[1] == "WHEAT":
                    feed_bought += int(m[2])
                    
            return action

        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([tracking_agent, "starter"])
        
        steps = env.steps
        reward = float(steps[-1][0].get("reward") or 0.0)
        final_obs = steps[-1][0]["observation"]
        final_farm = final_obs["farms"][0]
        final_money = float(final_farm.get("money") or 0.0)
        final_shed = dict((final_obs.get("private") or {}).get("shed") or {})
        final_hands = len(final_farm.get("hands") or [])
        
        # Count sales
        sales = defaultdict(int)
        for s in range(1, len(steps)):
            act = steps[s][0].get("action") or {}
            for o in (act.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                    sales[o[1]] += int(o[2])
                    
        # Bush-days and watering %
        tot_bush_days = sum(daily_bush_count.values())
        tot_watered_days = sum(daily_watered_count.values())
        water_rate = (tot_watered_days / tot_bush_days * 100.0) if tot_bush_days > 0 else 0.0
        
        # Terminal field state
        final_tiles = final_farm.get("tiles") or []
        straw_tiles_end = sum(1 for r in final_tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
        
        return {
            "arm_id": arm_id, "seed": seed, "reward": reward,
            "terminal_money": final_money,
            "straw_harvested": straw_harvested,
            "straw_sold": sales.get("STRAWBERRY", 0),
            "wool_harvested": wool_harvested,
            "wool_sold": sales.get("WOOL", 0),
            "milk_harvested": milk_harvested,
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "melon_sold": sales.get("MELON", 0),
            "fert_sold": sales.get("FERTILIZER", 0),
            "fert_applied": fert_applied,
            "fert_collected": fert_collected,
            "feed_bought": feed_bought,
            "moves_count": moves_count,
            "prod_count": prod_count,
            "idle_count": idle_count,
            "tot_bush_days": tot_bush_days,
            "tot_watered_days": tot_watered_days,
            "watering_rate_pct": water_rate,
            "straw_tiles_end": straw_tiles_end,
            "final_hands": final_hands,
            "shed_max": shed_max,
            "shed_terminal": sum(final_shed.values()),
            "error": None
        }
    except Exception as e:
        return {"arm_id": arm_id, "seed": seed, "reward": 0.0, "error": str(e)}

def run_experiment(seeds=range(1000, 1050), max_workers=10):
    print(f"Starting Strawberry Capacity Experiment on {len(seeds)} seeds ({seeds[0]}-{seeds[-1]})...")
    start_time = time.time()
    
    tasks = []
    for arm_id, (mod_path, cls_name, disp_name) in VARIANT_MODULES.items():
        for s in seeds:
            tasks.append((arm_id, mod_path, cls_name, s))
            
    print(f"Total simulations to run: {len(tasks)} across 6 arms...")
    results_by_arm = defaultdict(list)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_eval_single_seed, t): t for t in tasks}
        done_cnt = 0
        for fut in as_completed(futures):
            res = fut.result()
            results_by_arm[res["arm_id"]].append(res)
            done_cnt += 1
            if done_cnt % 25 == 0 or done_cnt == len(tasks):
                elapsed = time.time() - start_time
                print(f"Progress: {done_cnt}/{len(tasks)} completed ({elapsed:.1f}s)...")
                
    elapsed = time.time() - start_time
    print(f"\nAll {len(tasks)} runs completed in {elapsed:.1f}s ({elapsed/len(tasks):.2f}s per sim).")
    
    # Analyze and summarize results
    summary = {}
    base_results = {r["seed"]: r["reward"] for r in results_by_arm["ARM_A"]}
    
    for arm_id, (mod_path, cls_name, disp_name) in VARIANT_MODULES.items():
        arm_res = results_by_arm[arm_id]
        rewards = [r["reward"] for r in arm_res if r["error"] is None]
        straw_sold = [r["straw_sold"] for r in arm_res if r["error"] is None]
        straw_harv = [r["straw_harvested"] for r in arm_res if r["error"] is None]
        wool_sold = [r["wool_sold"] for r in arm_res if r["error"] is None]
        milk_sold = [r["milk_sold"] for r in arm_res if r["error"] is None]
        wheat_sold = [r["wheat_sold"] for r in arm_res if r["error"] is None]
        water_rate = [r["watering_rate_pct"] for r in arm_res if r["error"] is None]
        moves = [r["moves_count"] for r in arm_res if r["error"] is None]
        prods = [r["prod_count"] for r in arm_res if r["error"] is None]
        idles = [r["idle_count"] for r in arm_res if r["error"] is None]
        bush_days = [r["tot_bush_days"] for r in arm_res if r["error"] is None]
        feed_bought = [r["feed_bought"] for r in arm_res if r["error"] is None]
        fert_applied = [r["fert_applied"] for r in arm_res if r["error"] is None]
        
        # Win rate vs Base
        wins = 0
        ties = 0
        for r in arm_res:
            s = r["seed"]
            if s in base_results:
                if r["reward"] > base_results[s]: wins += 1
                elif r["reward"] == base_results[s]: ties += 1
        win_rate = (wins + 0.5 * ties) / len(arm_res) * 100.0 if arm_res else 0.0
        
        mean_r = float(np.mean(rewards)) if rewards else 0.0
        med_r = float(np.median(rewards)) if rewards else 0.0
        std_r = float(np.std(rewards)) if rewards else 0.0
        ci95 = 1.96 * std_r / np.sqrt(len(rewards)) if rewards else 0.0
        
        summary[arm_id] = {
            "name": disp_name,
            "mean_reward": mean_r,
            "median_reward": med_r,
            "std_reward": std_r,
            "ci95": ci95,
            "win_rate_vs_base": win_rate,
            "mean_straw_sold": float(np.mean(straw_sold)),
            "mean_straw_harvested": float(np.mean(straw_harv)),
            "mean_wool_sold": float(np.mean(wool_sold)),
            "mean_milk_sold": float(np.mean(milk_sold)),
            "mean_wheat_sold": float(np.mean(wheat_sold)),
            "mean_watering_rate": float(np.mean(water_rate)),
            "mean_bush_days": float(np.mean(bush_days)),
            "mean_moves": float(np.mean(moves)),
            "mean_prod": float(np.mean(prods)),
            "mean_idle": float(np.mean(idles)),
            "mean_feed_bought": float(np.mean(feed_bought)),
            "mean_fert_applied": float(np.mean(fert_applied)),
        }
        
    # Print formatted comparison table
    print("\n" + "="*110)
    print("STRAWBERRY CAPACITY & IRRIGATION EXPERIMENT RESULTS (50 MATCHED SEEDS: 1000-1049)")
    print("="*110)
    print(f"{'ARM':<8} {'VARIANT NAME':<24} {'MEAN REWARD ($)':<16} {'95% CI':<12} {'MEDIAN ($)':<14} {'WIN %':<8} {'STRAW':<8} {'WOOL':<8} {'WATER %':<8}")
    print("-"*110)
    for arm_id in ["ARM_A", "ARM_B", "ARM_C", "ARM_D", "ARM_E", "ARM_F"]:
        s = summary[arm_id]
        print(f"{arm_id:<8} {s['name']:<24} ${s['mean_reward']:>12,.2f}  ±${s['ci95']:>7,.2f}  ${s['median_reward']:>10,.2f}  {s['win_rate_vs_base']:>5.1f}%  {s['mean_straw_sold']:>6.1f}u  {s['mean_wool_sold']:>6.1f}u  {s['mean_watering_rate']:>6.1f}%")
    print("="*110)
    
    os.makedirs("scratch", exist_ok=True)
    out_path = "scratch/strawberry_capacity_experiment_results.json"
    with open(out_path, "w") as f:
        json.dump({"summary": summary, "raw_results": results_by_arm}, f, indent=2)
    print(f"\nSaved full results to {out_path}")
    return summary

if __name__ == "__main__":
    run_experiment(range(1000, 1050), max_workers=10)
