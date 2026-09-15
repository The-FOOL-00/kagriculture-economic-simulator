"""
scratch/run_clean_discovery_grid.py
===================================
Pre-Registered Discovery Grid Sweep across 500 Fresh Seeds (930,001 to 930,500).
Evaluates 10 structured configurations around the candidate parameters:
  - Deficit variation: 1500.0, 2000.0, 2500.0
  - Delta variation: 2.0, 4.0, 6.0
  - Batch variation: 8, 12, 16
  - Corners: Full aggressive [1500, 2, 16] and Conservative [2500, 6, 8]
  - Baseline V54++: [4000, 8, 8]

Computes paired deltas vs Baseline V54++, bootstrap CIs, and applies
the pre-registered selection rule.
"""

import os
import sys
import copy
import json
import time
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util

GRID_ARMS = {
    "Baseline_V54pp": {"preempt_money_deficit": 4000.0, "preempt_minimum_delta": 8.0, "preempt_maximum_batch": 8},
    "G1_Cand_2000_4_12": {"preempt_money_deficit": 2000.0, "preempt_minimum_delta": 4.0, "preempt_maximum_batch": 12},
    "G2_Deficit_1500": {"preempt_money_deficit": 1500.0, "preempt_minimum_delta": 4.0, "preempt_maximum_batch": 12},
    "G3_Deficit_2500": {"preempt_money_deficit": 2500.0, "preempt_minimum_delta": 4.0, "preempt_maximum_batch": 12},
    "G4_Delta_2": {"preempt_money_deficit": 2000.0, "preempt_minimum_delta": 2.0, "preempt_maximum_batch": 12},
    "G5_Delta_6": {"preempt_money_deficit": 2000.0, "preempt_minimum_delta": 6.0, "preempt_maximum_batch": 12},
    "G6_Batch_8": {"preempt_money_deficit": 2000.0, "preempt_minimum_delta": 4.0, "preempt_maximum_batch": 8},
    "G7_Batch_16": {"preempt_money_deficit": 2000.0, "preempt_minimum_delta": 4.0, "preempt_maximum_batch": 16},
    "G8_Agg_Corner": {"preempt_money_deficit": 1500.0, "preempt_minimum_delta": 2.0, "preempt_maximum_batch": 16},
    "G9_Cons_Corner": {"preempt_money_deficit": 2500.0, "preempt_minimum_delta": 6.0, "preempt_maximum_batch": 8},
}

def load_v66():
    path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    spec = importlib.util.spec_from_file_location("v66_agent_grid", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", getattr(mod, "kaggle_agent", None))

def run_grid_seed(args):
    seed, arm_name, params = args
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    from scratch.instrumented_v54_plus import InstrumentedV54Plus

    # Build agent with specific grid parameters
    agent_inst = InstrumentedV54Plus()
    # update config
    for k, v in params.items():
        agent_inst.config_dict[k] = v
    agent_inst.v51_config = agent_inst.policies["backbone"].residual_config.__class__(**agent_inst.config_dict)
    for rname in agent_inst.policies:
        p = agent_inst.policies[rname]
        if hasattr(p, "controller"):
            p.controller.config = agent_inst.v51_config

    v66 = load_v66()

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = agent_inst(o0)
        a1 = v66(o1)
        env.step([a0, a1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    return {
        "seed": seed,
        "arm": arm_name,
        "r0": r0,
        "r1": r1,
        "margin": r0 - r1,
    }

def bootstrap_ci(arr, n_boot=2000, ci=0.95):
    if len(arr) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(12345)
    boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot, alpha * 100)), float(np.percentile(boot, (1.0 - alpha) * 100)))

def main():
    seeds = list(range(930001, 930501)) # 500 fresh discovery seeds
    print(f"=== CLEAN DISCOVERY GRID SWEEP across {len(seeds)} fresh seeds ({seeds[0]}–{seeds[-1]}) ===")
    print(f"Testing {len(GRID_ARMS)} configurations using 12 workers...")

    tasks = []
    for arm_name, params in GRID_ARMS.items():
        for seed in seeds:
            tasks.append((seed, arm_name, params))

    t0 = time.time()
    results_by_arm = defaultdict(dict)

    with ProcessPoolExecutor(max_workers=12) as executor:
        for i, res in enumerate(executor.map(run_grid_seed, tasks), 1):
            results_by_arm[res["arm"]][res["seed"]] = res
            if i % 500 == 0 or i == len(tasks):
                elapsed = time.time() - t0
                print(f"  Completed {i}/{len(tasks)} matches ({elapsed:.1f}s, {elapsed/i:.2f}s/match)...")

    # Paired deltas relative to Baseline_V54pp
    baseline_rewards = np.array([results_by_arm["Baseline_V54pp"][s]["r0"] for s in seeds])
    baseline_margins = np.array([results_by_arm["Baseline_V54pp"][s]["margin"] for s in seeds])

    grid_summary = {}

    print("\n--- PRE-REGISTERED DISCOVERY GRID RESULTS (vs Baseline V54++) ---")
    header = f"{'Configuration':<20} | {'Mean Delta':<11} | {'Median':<9} | {'95% CI':<20} | {'W/L/T':<10} | {'P(<-$1k)':<9} | {'P(>+$200)':<9}"
    print(header)
    print("-" * 95)

    for arm_name, params in GRID_ARMS.items():
        if arm_name == "Baseline_V54pp":
            continue
        arm_rewards = np.array([results_by_arm[arm_name][s]["r0"] for s in seeds])
        deltas = arm_rewards - baseline_rewards

        mean_d = float(np.mean(deltas))
        med_d = float(np.median(deltas))
        ci_low, ci_high = bootstrap_ci(deltas)
        wins = int(np.sum(deltas > 0))
        losses = int(np.sum(deltas < 0))
        ties = int(np.sum(deltas == 0))

        p_loss_1000 = float(np.mean(deltas < -1000.0) * 100.0)
        p_gain_200 = float(np.mean(deltas > 200.0) * 100.0)

        grid_summary[arm_name] = {
            "params": params,
            "mean_delta": mean_d,
            "median_delta": med_d,
            "ci_95": [ci_low, ci_high],
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "p_loss_1000": p_loss_1000,
            "p_gain_200": p_gain_200,
        }

        print(
            f"{arm_name:<20} | {mean_d:+10.2f} | {med_d:+8.1f} | "
            f"[{ci_low:+8.2f}, {ci_high:+8.2f}] | "
            f"{wins:>3}/{losses:>3}/{ties:>3} | {p_loss_1000:>7.1f}% | {p_gain_200:>7.1f}%"
        )

    # Apply pre-registered selection rule:
    # argmax Lower Bound of 95% Bootstrap CI subject to:
    # 1. Mean delta > 0
    # 2. Lower CI > 0
    # 3. P(delta < -1000) <= 1.0%
    qualifying = []
    for name, s in grid_summary.items():
        if s["mean_delta"] > 0 and s["ci_95"][0] > 0 and s["p_loss_1000"] <= 1.0:
            qualifying.append((s["ci_95"][0], name, s))

    qualifying.sort(reverse=True)
    if qualifying:
        winner_ci_low, winner_name, winner_stats = qualifying[0]
        print(f"\nWINNING CONFIGURATION BY PRE-REGISTERED RULE: {winner_name}")
        print(f"  Params: {winner_stats['params']}")
        print(f"  Lower 95% CI: {winner_ci_low:+.2f} | Mean Delta: {winner_stats['mean_delta']:+.2f}")
    else:
        print("\nNO CONFIGURATION QUALIFIED UNDER SELECTION RULE.")
        winner_name = None

    out_file = os.path.join(BASE_DIR, "research", "residual_clean_discovery_grid.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "seeds": [seeds[0], seeds[-1]],
            "num_seeds": len(seeds),
            "baseline_mean_reward": float(np.mean(baseline_rewards)),
            "baseline_mean_margin": float(np.mean(baseline_margins)),
            "grid_results": grid_summary,
            "winning_arm": winner_name,
        }, f, indent=2)
    print(f"Discovery grid results saved to {out_file}")

if __name__ == "__main__":
    main()
