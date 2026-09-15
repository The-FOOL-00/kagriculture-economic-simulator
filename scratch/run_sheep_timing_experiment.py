"""
Phase 1: Sheep Timing Experiment Runner
=======================================
Runs 50 matched seeds (1000-1049) across 5 controlled sheep timing variants:
- Arm 1A: Baseline Sheep (~Day 16)
- Arm 1B: Day 9 Sheep (Target 6 by Day 9)
- Arm 1C: Day 11 Sheep (Target 6 by Day 11)
- Arm 1D: Day 13 Sheep (Target 6 by Day 13)
- Arm 1E: Late Sheep (Day 18+)

Tracks full daily cash trajectories, sheep counts, cow counts, strawberry output,
feed purchases, and opportunity costs.
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
from scratch.sheep_timing_variants import (
    Variant1A_BaselineSheep, Variant1B_Day9Sheep,
    Variant1C_Day11Sheep, Variant1D_Day13Sheep,
    Variant1E_Late18Sheep
)

SHEEP_ARMS = {
    "ARM_1A": (Variant1A_BaselineSheep, "Baseline-Sheep-Day16"),
    "ARM_1B": (Variant1B_Day9Sheep, "Early-Sheep-Day9"),
    "ARM_1C": (Variant1C_Day11Sheep, "Inter-Sheep-Day11"),
    "ARM_1D": (Variant1D_Day13Sheep, "Inter-Sheep-Day13"),
    "ARM_1E": (Variant1E_Late18Sheep, "Late-Sheep-Day18"),
}

CHECKPOINT_DAYS = [4, 8, 12, 16, 20, 24, 28]

def _eval_single_sheep_seed(args):
    arm_id, seed = args
    cls_factory, disp_name = SHEEP_ARMS[arm_id]
    agent_instance = cls_factory()
    
    try:
        cash_history = {}
        sheep_by_day = {}
        cows_by_day = {}
        feed_bought = 0
        fert_collected = 0
        fert_applied = 0
        moves_count = 0
        prod_count = 0
        idle_count = 0
        straw_harvested = 0
        wool_harvested = 0
        milk_harvested = 0
        last_invs = None
        insolvency_events = 0

        def tracking_agent(obs, cfg=None):
            nonlocal feed_bought, fert_collected, fert_applied, moves_count, prod_count, idle_count
            nonlocal straw_harvested, wool_harvested, milk_harvested, last_invs, insolvency_events
            
            step = obs["step"]
            day = obs.get("day", step // 24)
            hour = obs.get("hour", step % 24)
            farm = obs["farms"][0]
            money = float(farm.get("money") or 0.0)
            if money < 0: insolvency_events += 1

            # Checkpoint cash & animal counts at hour 23
            if hour == 23:
                tiles = farm.get("tiles") or []
                c = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
                s = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
                sheep_by_day[day] = s
                cows_by_day[day] = c
                if day in CHECKPOINT_DAYS:
                    cash_history[day] = money

            curr_invs = copy.deepcopy((obs.get("private") or {}).get("inventories") or [])
            if last_invs is not None:
                for ci, li in zip(curr_invs, last_invs):
                    ds = ci.get("STRAWBERRY", 0) - li.get("STRAWBERRY", 0)
                    if ds > 0: straw_harvested += ds
                    dw = ci.get("WOOL", 0) - li.get("WOOL", 0)
                    if dw > 0: wool_harvested += dw
                    dm = ci.get("MILK", 0) - li.get("MILK", 0)
                    if dm > 0: milk_harvested += dm
            last_invs = curr_invs

            action = agent_instance(obs, cfg)

            all_acts = [action.get("farmer")] + (action.get("hands") or [])
            for a in all_acts:
                if isinstance(a, list) and len(a) > 0:
                    cmd = a[0]
                    if cmd in ("NORTH", "SOUTH", "EAST", "WEST"): moves_count += 1
                    elif cmd == "PASS": idle_count += 1
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

        # Sales from market orders
        sales = defaultdict(int)
        for s in range(1, len(steps)):
            act = steps[s][0].get("action") or {}
            for o in (act.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                    sales[o[1]] += int(o[2])

        return {
            "arm_id": arm_id, "seed": seed, "reward": reward,
            "terminal_money": final_money,
            "straw_sold": sales.get("STRAWBERRY", 0),
            "straw_harvested": straw_harvested,
            "wool_sold": sales.get("WOOL", 0),
            "wool_harvested": wool_harvested,
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "fert_sold": sales.get("FERTILIZER", 0),
            "fert_applied": fert_applied,
            "feed_bought": feed_bought,
            "cash_history": cash_history,
            "sheep_by_day": sheep_by_day,
            "cows_by_day": cows_by_day,
            "moves_count": moves_count,
            "prod_count": prod_count,
            "idle_count": idle_count,
            "insolvency_events": insolvency_events,
            "error": None
        }
    except Exception as e:
        return {"arm_id": arm_id, "seed": seed, "reward": 0.0, "error": str(e)}

def run_sheep_experiment(seeds=range(1000, 1050), max_workers=10):
    print("="*100)
    print(f"PHASE 1: SHEEP TIMING EXPERIMENT ({len(seeds)} SEEDS: {seeds[0]}-{seeds[-1]})")
    print("="*100)
    start_time = time.time()
    
    tasks = []
    for arm_id in SHEEP_ARMS:
        for s in seeds:
            tasks.append((arm_id, s))
            
    results_by_arm = defaultdict(list)
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_eval_single_sheep_seed, t): t for t in tasks}
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results_by_arm[r["arm_id"]].append(r)
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"Progress: {done}/{len(tasks)} runs completed ({time.time() - start_time:.1f}s)...")
                
    elapsed = time.time() - start_time
    print(f"All {len(tasks)} runs completed in {elapsed:.1f}s.\n")

    summary = {}
    base_res = {r["seed"]: r["reward"] for r in results_by_arm["ARM_1A"]}
    
    for arm_id, (cls_factory, disp_name) in SHEEP_ARMS.items():
        res_list = results_by_arm[arm_id]
        rewards = [r["reward"] for r in res_list if r["error"] is None]
        straw_sold = [r["straw_sold"] for r in res_list if r["error"] is None]
        wool_sold = [r["wool_sold"] for r in res_list if r["error"] is None]
        milk_sold = [r["milk_sold"] for r in res_list if r["error"] is None]
        wheat_sold = [r["wheat_sold"] for r in res_list if r["error"] is None]
        feed_bgt = [r["feed_bought"] for r in res_list if r["error"] is None]
        fert_sold = [r["fert_sold"] for r in res_list if r["error"] is None]
        
        # Average cash trajectory
        avg_cash = {}
        for d in CHECKPOINT_DAYS:
            c_vals = [r["cash_history"].get(d, 0) for r in res_list if r["error"] is None]
            avg_cash[d] = float(np.mean(c_vals)) if c_vals else 0.0

        # Average sheep count on Days 7, 9, 11, 13, 16
        avg_sheep = {}
        for d in [5, 7, 9, 11, 13, 15, 17, 20]:
            s_vals = [r["sheep_by_day"].get(d, 0) for r in res_list if r["error"] is None]
            avg_sheep[d] = float(np.mean(s_vals)) if s_vals else 0.0
            
        avg_cows = {}
        for d in [5, 7, 9, 11, 13, 15, 17, 20]:
            c_vals = [r["cows_by_day"].get(d, 0) for r in res_list if r["error"] is None]
            avg_cows[d] = float(np.mean(c_vals)) if c_vals else 0.0

        wins = sum(1 for r in res_list if r["reward"] > base_res.get(r["seed"], 0))
        ties = sum(1 for r in res_list if r["reward"] == base_res.get(r["seed"], 0))
        win_rate = (wins + 0.5 * ties) / len(res_list) * 100.0

        mean_r, std_r, med_r = np.mean(rewards), np.std(rewards), np.median(rewards)
        ci95 = 1.96 * std_r / np.sqrt(len(rewards))

        summary[arm_id] = {
            "name": disp_name,
            "mean_reward": float(mean_r),
            "median_reward": float(med_r),
            "std_reward": float(std_r),
            "ci95": float(ci95),
            "win_rate_vs_base": float(win_rate),
            "mean_straw_sold": float(np.mean(straw_sold)),
            "mean_wool_sold": float(np.mean(wool_sold)),
            "mean_milk_sold": float(np.mean(milk_sold)),
            "mean_wheat_sold": float(np.mean(wheat_sold)),
            "mean_feed_bought": float(np.mean(feed_bgt)),
            "mean_fert_sold": float(np.mean(fert_sold)),
            "avg_cash_trajectory": avg_cash,
            "avg_sheep_trajectory": avg_sheep,
            "avg_cows_trajectory": avg_cows,
        }

    print("="*110)
    print("PHASE 1: SHEEP TIMING EXPERIMENTAL RESULTS (50 SEEDS)")
    print("="*110)
    print(f"{'ARM':<8} {'VARIANT NAME':<24} {'MEAN REWARD ($)':<16} {'95% CI':<12} {'MEDIAN ($)':<14} {'WIN %':<8} {'WOOL':<8} {'STRAW':<8} {'FEED BGT':<10}")
    print("-"*110)
    for arm_id in ["ARM_1A", "ARM_1B", "ARM_1C", "ARM_1D", "ARM_1E"]:
        s = summary[arm_id]
        print(f"{arm_id:<8} {s['name']:<24} ${s['mean_reward']:>12,.2f}  ±${s['ci95']:>7,.2f}  ${s['median_reward']:>10,.2f}  {s['win_rate_vs_base']:>5.1f}%  {s['mean_wool_sold']:>6.1f}u  {s['mean_straw_sold']:>6.1f}u  {s['mean_feed_bought']:>7.1f}u")
    print("="*110)
    
    print("\nSHEEP COUNT PROGRESSION BY DAY (MEAN):")
    print(f"{'ARM':<8} {'VARIANT':<22} {'D5':<6} {'D7':<6} {'D9':<6} {'D11':<6} {'D13':<6} {'D15':<6} {'D17':<6}")
    for arm_id in ["ARM_1A", "ARM_1B", "ARM_1C", "ARM_1D", "ARM_1E"]:
        s = summary[arm_id]
        sh = s["avg_sheep_trajectory"]
        print(f"{arm_id:<8} {s['name']:<22} {sh.get(5,0):>4.1f}   {sh.get(7,0):>4.1f}   {sh.get(9,0):>4.1f}   {sh.get(11,0):>4.1f}   {sh.get(13,0):>4.1f}   {sh.get(15,0):>4.1f}   {sh.get(17,0):>4.1f}")
        
    print("\nCOW COUNT PROGRESSION BY DAY (MEAN):")
    print(f"{'ARM':<8} {'VARIANT':<22} {'D5':<6} {'D7':<6} {'D9':<6} {'D11':<6} {'D13':<6} {'D15':<6} {'D17':<6}")
    for arm_id in ["ARM_1A", "ARM_1B", "ARM_1C", "ARM_1D", "ARM_1E"]:
        s = summary[arm_id]
        cw = s["avg_cows_trajectory"]
        print(f"{arm_id:<8} {s['name']:<22} {cw.get(5,0):>4.1f}   {cw.get(7,0):>4.1f}   {cw.get(9,0):>4.1f}   {cw.get(11,0):>4.1f}   {cw.get(13,0):>4.1f}   {cw.get(15,0):>4.1f}   {cw.get(17,0):>4.1f}")

    print("\nCASH TRAJECTORY ($) BY DAY (MEAN):")
    print(f"{'ARM':<8} {'VARIANT':<22} {'D4':<8} {'D8':<8} {'D12':<8} {'D16':<8} {'D20':<8} {'D24':<8} {'D28':<8}")
    for arm_id in ["ARM_1A", "ARM_1B", "ARM_1C", "ARM_1D", "ARM_1E"]:
        s = summary[arm_id]
        cs = s["avg_cash_trajectory"]
        print(f"{arm_id:<8} {s['name']:<22} ${cs.get(4,0):>6.0f}  ${cs.get(8,0):>6.0f}  ${cs.get(12,0):>6.0f}  ${cs.get(16,0):>6.0f}  ${cs.get(20,0):>6.0f}  ${cs.get(24,0):>6.0f}  ${cs.get(28,0):>6.0f}")

    os.makedirs("scratch", exist_ok=True)
    out_file = "scratch/sheep_timing_experiment_results.json"
    with open(out_file, "w") as f:
        json.dump({"summary": summary, "raw_results": results_by_arm}, f, indent=2)
    print(f"\nSaved sheep timing experiment data to {out_file}")
    return summary

if __name__ == "__main__":
    run_sheep_experiment(range(1000, 1050), max_workers=10)
