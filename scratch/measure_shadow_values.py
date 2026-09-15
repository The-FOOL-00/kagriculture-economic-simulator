import sys
import os
import json
import copy
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Intercepting agent for Counterfactual Suppression
class CounterfactualSuppressionAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50, target_task=None, target_hour_range=None, suppress_limit=1):
        super().__init__(quota)
        self.target_task = target_task
        self.target_hour_range = target_hour_range  # tuple (start_step, end_step)
        self.suppress_limit = suppress_limit
        self.suppressed_count = 0
        self.suppression_events = []

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        p0_act = super().__call__(obs, config)

        if self.target_task is None or self.target_hour_range is None:
            return p0_act

        start_step, end_step = self.target_hour_range
        if not (start_step <= step < end_step):
            return p0_act

        if self.suppressed_count >= self.suppress_limit:
            return p0_act

        p = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm = farms[p] if p < len(farms) else {}
        tiles = farm.get("tiles") or []
        farmer_pos = farm.get("farmer")
        hands_pos = farm.get("hands") or []
        all_workers = [farmer_pos] + hands_pos

        f_act = p0_act.get("farmer")
        h_acts = list(p0_act.get("hands") or [])
        all_actions = [f_act] + h_acts

        # Check for target_task
        for w_idx, (w_pos, act) in enumerate(zip(all_workers, all_actions)):
            if not act or not isinstance(act, list):
                continue
            op = act[0]
            matched = False

            if self.target_task == "HARVEST_STRAWBERRY":
                if op == "HARVEST" and w_pos:
                    t = tiles[w_pos[1]][w_pos[0]] if w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]]) else None
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        matched = True
            elif self.target_task == "HARVEST_WHEAT":
                if op == "HARVEST" and w_pos:
                    t = tiles[w_pos[1]][w_pos[0]] if w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]]) else None
                    if isinstance(t, dict) and t.get("crop") == "WHEAT":
                        matched = True
            elif self.target_task == "PLANT_STRAWBERRY":
                if op == "PLANT" and len(act) > 1 and act[1] == "STRAWBERRY":
                    matched = True
            elif self.target_task == "PLANT_WHEAT":
                if op == "PLANT" and len(act) > 1 and act[1] == "WHEAT":
                    matched = True
            elif self.target_task == "WATER":
                if op == "WATER":
                    matched = True
            elif self.target_task == "CLEAR_OBSTACLE":
                if op == "DIG":
                    matched = True
            elif self.target_task == "BUILD_PASTURE":
                if op == "BUILD_PASTURE":
                    matched = True
            elif self.target_task == "FEED":
                if op == "FEED":
                    matched = True
            elif self.target_task == "CARE":
                if op == "CARE":
                    matched = True
            elif self.target_task == "PLACE_ANIMAL":
                if op == "PLACE":
                    matched = True

            if matched:
                # Suppress this action -> convert to PASS
                if w_idx == 0:
                    p0_act["farmer"] = ["PASS"]
                else:
                    h_acts[w_idx - 1] = ["PASS"]
                    p0_act["hands"] = h_acts
                self.suppressed_count += 1
                self.suppression_events.append((step, w_idx, self.target_task, w_pos))
                if self.suppressed_count >= self.suppress_limit:
                    break

        return p0_act

def eval_single_suppression_with_base(args):
    seed, task, day_range, base_reward = args
    quota = 50
    start_step = day_range[0] * 24
    end_step = day_range[1] * 24

    cfg = {"episodeSteps": 720, "seed": seed}
    agent_cf = CounterfactualSuppressionAgent(quota, target_task=task, target_hour_range=(start_step, end_step), suppress_limit=1)
    env_cf = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_cf = env_cf.run([agent_cf, "starter"])
    cf_reward = float(steps_cf[-1][0]["reward"])

    shadow_val = base_reward - cf_reward
    was_suppressed = (agent_cf.suppressed_count > 0)

    return {
        "seed": seed,
        "task": task,
        "day_range": day_range,
        "base_reward": base_reward,
        "cf_reward": cf_reward,
        "shadow_val": shadow_val,
        "was_suppressed": was_suppressed
    }

def run_base_q50_with_trace(seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env_base = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_base = env_base.run([ParameterizedQuotaAgent(50), "starter"])
    rew = float(steps_base[-1][0]["reward"])

    # Extract which tasks executed in each day range
    executed_tasks = defaultdict(set) # day_range -> set of tasks
    day_ranges = [
        (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14)
    ]
    for s_idx, st in enumerate(steps_base):
        obs = st[0]["observation"]
        day = obs["day"]
        tiles = obs["farms"][0]["tiles"]
        workers = [obs["farms"][0].get("farmer")] + (obs["farms"][0].get("hands") or [])

        for d_r in day_ranges:
            if d_r[0] <= day < d_r[1]:
                act = st[0].get("action") or {}
                all_acts = [act.get("farmer")] + (act.get("hands") or [])
                for w_idx, a in enumerate(all_acts):
                    if a and isinstance(a, list):
                        op = a[0]
                        w_pos = workers[w_idx] if w_idx < len(workers) else None
                        t = tiles[w_pos[1]][w_pos[0]] if (w_pos and w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]])) else None
                        if op == "HARVEST" and isinstance(t, dict):
                            if t.get("crop") == "STRAWBERRY": executed_tasks[d_r].add("HARVEST_STRAWBERRY")
                            elif t.get("crop") == "WHEAT": executed_tasks[d_r].add("HARVEST_WHEAT")
                        elif op == "PLANT" and len(a) > 1:
                            if a[1] == "STRAWBERRY": executed_tasks[d_r].add("PLANT_STRAWBERRY")
                            elif a[1] == "WHEAT": executed_tasks[d_r].add("PLANT_WHEAT")
                        elif op == "WATER": executed_tasks[d_r].add("WATER")
                        elif op == "DIG": executed_tasks[d_r].add("CLEAR_OBSTACLE")
                        elif op == "BUILD_PASTURE": executed_tasks[d_r].add("BUILD_PASTURE")
                        elif op == "FEED": executed_tasks[d_r].add("FEED")
                        elif op == "CARE": executed_tasks[d_r].add("CARE")
                        elif op == "PLACE": executed_tasks[d_r].add("PLACE_ANIMAL")

    return seed, rew, {k: list(v) for k, v in executed_tasks.items()}

def run_shadow_price_study(seeds=range(1250, 1275)):
    day_ranges = [
        (8, 9),
        (9, 10),
        (10, 11),
        (11, 12),
        (12, 13),
        (13, 14)
    ]
    tasks = [
        "HARVEST_STRAWBERRY",
        "HARVEST_WHEAT",
        "PLANT_STRAWBERRY",
        "PLANT_WHEAT",
        "WATER",
        "CLEAR_OBSTACLE",
        "BUILD_PASTURE",
        "FEED",
        "CARE",
        "PLACE_ANIMAL"
    ]

    print(f"Precomputing baseline Q50 runs and task traces for {len(seeds)} seeds...")
    base_data = {}
    with ProcessPoolExecutor(max_workers=10) as executor:
        for seed, rew, tr in executor.map(run_base_q50_with_trace, seeds):
            base_data[seed] = (rew, tr)

    all_jobs = []
    for s in seeds:
        rew, tr = base_data[s]
        for d_r in day_ranges:
            exec_for_dr = tr.get(d_r, [])
            for t in exec_for_dr:
                all_jobs.append((s, t, d_r, rew))

    print(f"Running active counterfactual jobs: {len(all_jobs)} jobs (filtered from 1,500 candidates)...")
    results_by_key = defaultdict(list)

    with ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(eval_single_suppression_with_base, all_jobs, chunksize=5):
            if res["was_suppressed"]:
                key = (res["day_range"], res["task"])
                results_by_key[key].append(res["shadow_val"])

    print("\n" + "="*80)
    print("EMPIRICAL LABOR SHADOW VALUES ($ / Worker-Hour) BY TASK AND TIME")
    print("="*80)
    print(f"{'Day Range':<12} | {'Task':<20} | {'Count':<6} | {'Mean Shadow ($)':<16} | {'Median ($)':<12}")
    print("-" * 80)

    summary_records = []
    for d_r in day_ranges:
        for t in tasks:
            key = (d_r, t)
            vals = results_by_key.get(key, [])
            if vals:
                mean_v = float(np.mean(vals))
                med_v = float(np.median(vals))
                count = len(vals)
            else:
                mean_v = 0.0
                med_v = 0.0
                count = 0
            d_str = f"Days {d_r[0]}-{d_r[1]}"
            print(f"{d_str:<12} | {t:<20} | {count:<6} | ${mean_v:>14.2f} | ${med_v:>10.2f}")
            summary_records.append({
                "day_range": d_str,
                "task": t,
                "count": count,
                "mean_shadow": mean_v,
                "median_shadow": med_v
            })

    with open("scratch/shadow_price_results.json", "w") as f:
        json.dump(summary_records, f, indent=2)
    print("\nSaved shadow price table to scratch/shadow_price_results.json")

if __name__ == "__main__":
    run_shadow_price_study(seeds=range(1250, 1275))
