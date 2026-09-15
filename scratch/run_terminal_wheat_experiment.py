"""
Phase 2: Terminal Land Multiplexing Experiment Runner
=====================================================
Runs 50 matched seeds (1000-1049) across 4 controlled terminal wheat variants:
- Arm 2A: Baseline (No terminal wheat; wheat buying ends Day 24)
- Arm 2B: Conservative Terminal Wheat (Target 10 seeds on Days 25-26)
- Arm 2C: Full Terminal Wheat (Target 25 seeds on Days 25-26)
- Arm 2D: Optimized Terminal Wheat (Target 25 seeds + synchronized watering/harvest)
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
from scratch.terminal_wheat_variants import (
    Variant2A_NoTerminalWheat, Variant2B_ConservativeTerminalWheat,
    Variant2C_FullTerminalWheat, Variant2D_OptimizedTerminalWheat
)

WHEAT_ARMS = {
    "ARM_2A": (Variant2A_NoTerminalWheat, "Baseline-NoTerminalWheat"),
    "ARM_2B": (Variant2B_ConservativeTerminalWheat, "Conservative-Wheat-10"),
    "ARM_2C": (Variant2C_FullTerminalWheat, "Full-Wheat-25"),
    "ARM_2D": (Variant2D_OptimizedTerminalWheat, "Optimized-Wheat-25"),
}

def _eval_single_wheat_seed(args):
    arm_id, seed = args
    cls_factory, disp_name = WHEAT_ARMS[arm_id]
    agent_instance = cls_factory()

    try:
        wheat_harvested = 0
        straw_harvested = 0
        wool_harvested = 0
        milk_harvested = 0
        last_invs = None
        feed_bought = 0
        terminal_wheat_planted = 0
        shed_max = 0

        def tracking_agent(obs, cfg=None):
            nonlocal wheat_harvested, straw_harvested, wool_harvested, milk_harvested, last_invs
            nonlocal feed_bought, terminal_wheat_planted, shed_max

            step = obs["step"]
            day = obs.get("day", step // 24)
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            c_load = sum(shed.values())
            if c_load > shed_max: shed_max = c_load

            curr_invs = copy.deepcopy(priv.get("inventories") or [])
            if last_invs is not None:
                for ci, li in zip(curr_invs, last_invs):
                    dw = ci.get("WHEAT", 0) - li.get("WHEAT", 0)
                    if dw > 0: wheat_harvested += dw
                    ds = ci.get("STRAWBERRY", 0) - li.get("STRAWBERRY", 0)
                    if ds > 0: straw_harvested += ds
                    dwl = ci.get("WOOL", 0) - li.get("WOOL", 0)
                    if dwl > 0: wool_harvested += dwl
                    dm = ci.get("MILK", 0) - li.get("MILK", 0)
                    if dm > 0: milk_harvested += dm
            last_invs = curr_invs

            action = agent_instance(obs, cfg)

            all_acts = [action.get("farmer")] + (action.get("hands") or [])
            for a in all_acts:
                if isinstance(a, list) and len(a) > 1 and a[0] == "PLANT" and a[1] == "WHEAT":
                    if day >= 25: terminal_wheat_planted += 1

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
            "wool_sold": sales.get("WOOL", 0),
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "wheat_harvested": wheat_harvested,
            "terminal_wheat_planted": terminal_wheat_planted,
            "feed_bought": feed_bought,
            "shed_max": shed_max,
            "error": None
        }
    except Exception as e:
        return {"arm_id": arm_id, "seed": seed, "reward": 0.0, "error": str(e)}

def run_terminal_wheat_experiment(seeds=range(1000, 1050), max_workers=10):
    print("="*100)
    print(f"PHASE 2: TERMINAL WHEAT MULTIPLEXING EXPERIMENT ({len(seeds)} SEEDS: {seeds[0]}-{seeds[-1]})")
    print("="*100)
    start_time = time.time()

    tasks = []
    for arm_id in WHEAT_ARMS:
        for s in seeds:
            tasks.append((arm_id, s))

    results_by_arm = defaultdict(list)
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_eval_single_wheat_seed, t): t for t in tasks}
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results_by_arm[r["arm_id"]].append(r)
            done += 1
            if done % 40 == 0 or done == len(tasks):
                print(f"Progress: {done}/{len(tasks)} runs completed ({time.time() - start_time:.1f}s)...")

    elapsed = time.time() - start_time
    print(f"All {len(tasks)} runs completed in {elapsed:.1f}s.\n")

    summary = {}
    base_res = {r["seed"]: r["reward"] for r in results_by_arm["ARM_2A"]}

    for arm_id, (cls_factory, disp_name) in WHEAT_ARMS.items():
        res_list = results_by_arm[arm_id]
        rewards = [r["reward"] for r in res_list if r["error"] is None]
        straw_sold = [r["straw_sold"] for r in res_list if r["error"] is None]
        wool_sold = [r["wool_sold"] for r in res_list if r["error"] is None]
        milk_sold = [r["milk_sold"] for r in res_list if r["error"] is None]
        wheat_sold = [r["wheat_sold"] for r in res_list if r["error"] is None]
        wheat_harv = [r["wheat_harvested"] for r in res_list if r["error"] is None]
        term_planted = [r["terminal_wheat_planted"] for r in res_list if r["error"] is None]
        shed_max = [r["shed_max"] for r in res_list if r["error"] is None]

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
            "mean_wheat_sold": float(np.mean(wheat_sold)),
            "mean_wheat_harvested": float(np.mean(wheat_harv)),
            "mean_terminal_planted": float(np.mean(term_planted)),
            "mean_straw_sold": float(np.mean(straw_sold)),
            "mean_wool_sold": float(np.mean(wool_sold)),
            "mean_milk_sold": float(np.mean(milk_sold)),
            "mean_shed_max": float(np.mean(shed_max)),
        }

    print("="*110)
    print("PHASE 2: TERMINAL WHEAT EXPERIMENTAL RESULTS (50 SEEDS)")
    print("="*110)
    print(f"{'ARM':<8} {'VARIANT NAME':<26} {'MEAN REWARD ($)':<16} {'95% CI':<12} {'MEDIAN ($)':<14} {'WIN %':<8} {'WHEAT SOLD':<12} {'TERM PLANTED':<14}")
    print("-"*110)
    for arm_id in ["ARM_2A", "ARM_2B", "ARM_2C", "ARM_2D"]:
        s = summary[arm_id]
        print(f"{arm_id:<8} {s['name']:<26} ${s['mean_reward']:>12,.2f}  ±${s['ci95']:>7,.2f}  ${s['median_reward']:>10,.2f}  {s['win_rate_vs_base']:>5.1f}%  {s['mean_wheat_sold']:>8.1f}u      {s['mean_terminal_planted']:>8.1f} tiles")
    print("="*110)

    os.makedirs("scratch", exist_ok=True)
    out_file = "scratch/terminal_wheat_experiment_results.json"
    with open(out_file, "w") as f:
        json.dump({"summary": summary, "raw_results": results_by_arm}, f, indent=2)
    print(f"\nSaved terminal wheat experiment data to {out_file}")
    return summary

if __name__ == "__main__":
    run_terminal_wheat_experiment(range(1000, 1050), max_workers=10)
