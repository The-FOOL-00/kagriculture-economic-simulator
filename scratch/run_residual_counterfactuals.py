"""
scratch/run_residual_counterfactuals.py
=======================================
Paired Counterfactual Gauntlet across fresh seeds for all residual mechanisms:
  R0: Baseline V54++
  R1: Disable Deficit Fronting (front_money_deficit = 1e6, front_on_near = False)
  R1_agg: Aggressive Deficit Fronting (front_money_deficit = 2000.0)
  R1_cons: Conservative Deficit Fronting (front_money_deficit = 7000.0)
  R1_near: Disable Front On Near Only
  R2: Disable Market Preemption (preempt_enabled = False)
  R2_agg: Aggressive Market Preemption (preempt_money_deficit = 2000.0, delta = 4.0, batch = 12)
  R2_cons: Conservative Market Preemption (preempt_money_deficit = 6000.0, delta = 16.0, batch = 4)
  R2_near: Disable Preempt On Near Only
  R3: Disable Strawberry Seed Trim
  R4: Disable Hour-23 Shed Guard
  R5: Disable Terminal Unit Recall (steps 713-716)
  R6: Disable Terminal Unit Home Convergence (steps 717-718)
  R7: Disable Terminal Market Liquidation (step 718)
  R8: Disable Weed Repair
  T1: All Terminal Overlays Disabled
  T2: Terminal Recall Earlier (711-716)
  T3: Terminal Recall Later (715-716)

Computes paired stats, bootstrap CIs, regime breakdown, tail-risk probabilities,
and verifies macro route synchronization (route divergence == 0.0%).
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

INTERVENTIONS = {
    "R0_baseline": {},
    "R1_disable_fronting": {"disable_fronting": True},
    "R1_agg_fronting": {"aggressive_fronting": True},
    "R1_cons_fronting": {"conservative_fronting": True},
    "R1_disable_front_near": {"disable_front_on_near": True},
    "R2_disable_preempt": {"disable_preempt": True},
    "R2_agg_preempt": {"aggressive_preempt": True},
    "R2_cons_preempt": {"conservative_preempt": True},
    "R2_disable_preempt_near": {"disable_preempt_on_near": True},
    "R3_disable_seed_trim": {"disable_seed_trim": True},
    "R4_disable_shed_guard": {"disable_shed_guard": True},
    "R5_disable_terminal_recall": {"disable_terminal_loaded_units": True},
    "R6_disable_terminal_units": {"disable_terminal_units": True},
    "R7_disable_terminal_market": {"disable_terminal_market": True},
    "R8_disable_weed_repair": {"disable_weed_repair": True},
    "T1_disable_all_terminal": {
        "disable_terminal_loaded_units": True,
        "disable_terminal_units": True,
        "disable_terminal_market": True,
    },
}

def load_v66():
    path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    spec = importlib.util.spec_from_file_location("v66_agent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", getattr(mod, "kaggle_agent", None))

def run_paired_seed(args):
    seed, arm_name, switches = args
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    from scratch.instrumented_v54_plus import InstrumentedV54Plus

    v54p = InstrumentedV54Plus(switches=switches)
    v66 = load_v66()

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    route_names = []
    actions_tape = []

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = v54p(o0)
        a1 = v66(o1)
        route_names.append(v54p.shop_state[0]["route"])
        env.step([a0, a1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    return {
        "seed": seed,
        "arm": arm_name,
        "reward_v54p": r0,
        "reward_v66": r1,
        "margin": r0 - r1,
        "routes": route_names,
    }

def bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    if len(diffs) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(12345)
    boot_means = [
        np.mean(rng.choice(diffs, size=len(diffs), replace=True))
        for _ in range(n_boot)
    ]
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_means, alpha * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    return (low, high)

def main():
    # 100 fresh seeds: 900,501 to 900,600
    seeds = list(range(900501, 900601))
    print(f"Running Paired Counterfactual Gauntlet across {len(seeds)} fresh seeds ({seeds[0]}–{seeds[-1]})...")
    print(f"Testing {len(INTERVENTIONS)} intervention arms using 12 workers...")

    tasks = []
    for arm_name, switches in INTERVENTIONS.items():
        for seed in seeds:
            tasks.append((seed, arm_name, switches))

    t0 = time.time()
    results_by_arm = defaultdict(dict)

    with ProcessPoolExecutor(max_workers=12) as executor:
        for i, res in enumerate(executor.map(run_paired_seed, tasks), 1):
            results_by_arm[res["arm"]][res["seed"]] = res
            if i % 100 == 0 or i == len(tasks):
                elapsed = time.time() - t0
                print(f"Completed {i}/{len(tasks)} matches ({elapsed:.1f}s)...")

    # Verify Macro Synchronization: route prior choices must be identical across all arms!
    baseline_routes = {seed: results_by_arm["R0_baseline"][seed]["routes"] for seed in seeds}
    route_divergence_violations = 0

    for arm_name, arm_results in results_by_arm.items():
        if arm_name == "R0_baseline":
            continue
        for seed in seeds:
            if arm_results[seed]["routes"] != baseline_routes[seed]:
                route_divergence_violations += 1

    print(f"\nMacro Synchronization Check: Route Divergence Violations = {route_divergence_violations}")
    assert route_divergence_violations == 0, "FATAL: Macro route diverged in counterfactual intervention!"

    # Analyze paired deltas relative to R0_baseline
    analysis = {}
    r0_rewards = np.array([results_by_arm["R0_baseline"][seed]["reward_v54p"] for seed in seeds])
    r0_margins = np.array([results_by_arm["R0_baseline"][seed]["margin"] for seed in seeds])

    # Regimes based on baseline vs V66
    v66_win_mask = (r0_margins < -2000)
    close_mask = (np.abs(r0_margins) <= 2000)
    v54p_win_mask = (r0_margins > 2000)

    print("\n--- CAUSAL COUNTERFACTUAL GAUNTLET RESULTS ---")
    header = (
        f"{'Arm':<28} | {'Mean Delta':<11} | {'Median':<9} | {'95% CI':<19} | "
        f"{'W/L/T':<10} | {'P(<-$500)':<10} | {'P(<-$1k)':<9} | {'P(>+$2k)':<9}"
    )
    print(header)
    print("-" * 115)

    for arm_name in INTERVENTIONS.keys():
        if arm_name == "R0_baseline":
            continue
        arm_rewards = np.array([results_by_arm[arm_name][seed]["reward_v54p"] for seed in seeds])
        # Delta = Intervention - Baseline
        # Note: If disabling X causes Delta < 0, X has positive causal value!
        deltas = arm_rewards - r0_rewards

        mean_delta = float(np.mean(deltas))
        median_delta = float(np.median(deltas))
        ci_low, ci_high = bootstrap_ci(deltas)

        wins = int(np.sum(deltas > 0))
        losses = int(np.sum(deltas < 0))
        ties = int(np.sum(deltas == 0))

        p_loss_500 = float(np.mean(deltas < -500.0) * 100.0)
        p_loss_1000 = float(np.mean(deltas < -1000.0) * 100.0)
        p_gain_2000 = float(np.mean(deltas > 2000.0) * 100.0)

        # Regimes
        delta_v66_win = float(np.mean(deltas[v66_win_mask])) if np.sum(v66_win_mask) > 0 else 0.0
        delta_close = float(np.mean(deltas[close_mask])) if np.sum(close_mask) > 0 else 0.0
        delta_v54p_win = float(np.mean(deltas[v54p_win_mask])) if np.sum(v54p_win_mask) > 0 else 0.0

        analysis[arm_name] = {
            "mean_delta": mean_delta,
            "median_delta": median_delta,
            "ci_95": [ci_low, ci_high],
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "p_loss_500": p_loss_500,
            "p_loss_1000": p_loss_1000,
            "p_gain_2000": p_gain_2000,
            "regime_deltas": {
                "v66_win_regime": delta_v66_win,
                "close_regime": delta_close,
                "v54p_win_regime": delta_v54p_win,
            },
        }

        print(
            f"{arm_name:<28} | {mean_delta:+10.1f} | {median_delta:+8.1f} | "
            f"[{ci_low:+8.1f}, {ci_high:+8.1f}] | "
            f"{wins:>3}/{losses:>3}/{ties:>2} | {p_loss_500:>8.1f}% | {p_loss_1000:>7.1f}% | {p_gain_2000:>7.1f}%"
        )

    out_path = os.path.join(BASE_DIR, "research", "residual_counterfactual_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seed_range": [seeds[0], seeds[-1]],
                "num_seeds": len(seeds),
                "baseline_mean_reward": float(np.mean(r0_rewards)),
                "baseline_mean_margin": float(np.mean(r0_margins)),
                "macro_route_divergence": 0.0,
                "analysis": analysis,
            },
            f,
            indent=2,
        )
    print(f"\nCounterfactual results saved to {out_path}")

if __name__ == "__main__":
    main()
