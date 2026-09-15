"""
scratch/run_500_seed_census.py
==============================
High-throughput 500-seed census of all runtime residual mechanisms in V54++.
Evaluates across fresh seeds 900,001 to 900,500 against Canonical V66.
Computes:
  - Total firings & percentages
  - Unique seeds firing
  - Total actions changed
  - Pearson correlation with final reward
  - Influential mechanism ranking
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

def load_v66():
    path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    spec = importlib.util.spec_from_file_location("v66_agent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", getattr(mod, "kaggle_agent", None))

def run_census_seed(seed: int):
    import sys, os
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    from scratch.instrumented_v54_plus import InstrumentedV54Plus
    v54p = InstrumentedV54Plus()
    v66 = load_v66()

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = v54p(o0)
        a1 = v66(o1)
        env.step([a0, a1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    # Aggregate telemetry
    firings_count = defaultdict(int)
    actions_changed = defaultdict(int)
    commodity_firings = defaultdict(int)

    for record in v54p.telemetry_history:
        for mech, fired in record["firings"].items():
            if fired:
                firings_count[mech] += 1
        for mech, count in record["actions_changed"].items():
            actions_changed[mech] += count
        for item in record.get("preempt_commodities", []):
            commodity_firings[item] += 1

    return {
        "seed": seed,
        "reward_v54p": r0,
        "reward_v66": r1,
        "margin": r0 - r1,
        "firings": dict(firings_count),
        "actions_changed": dict(actions_changed),
        "commodity_firings": dict(commodity_firings),
        "total_turns": len(v54p.telemetry_history),
    }

def main():
    seeds = list(range(900001, 900501))  # 500 fresh seeds
    print(f"Starting 500-seed census across seeds {seeds[0]} to {seeds[-1]} using 12 workers...")
    t0 = time.time()

    results = []
    # Use ProcessPoolExecutor with 12 workers
    with ProcessPoolExecutor(max_workers=12) as executor:
        for i, res in enumerate(executor.map(run_census_seed, seeds), 1):
            results.append(res)
            if i % 50 == 0 or i == len(seeds):
                elapsed = time.time() - t0
                print(f"Completed {i}/{len(seeds)} matches ({elapsed:.1f}s, {elapsed/i:.2f}s/match)...")

    total_time = time.time() - t0
    print(f"All 500 matches completed in {total_time:.1f}s.")

    # Compute census statistics
    total_turns = len(results) * 719
    mechanism_keys = [
        "fixed_route",
        "weed_repair",
        "debt_repay",
        "market_preempt",
        "deficit_fronting",
        "seed_trim",
        "shed_guard",
        "terminal_loaded_units",
        "terminal_units",
        "terminal_market",
        "sanitizer",
        "emergency_fallback",
    ]

    stats = {}
    rewards = np.array([r["reward_v54p"] for r in results])
    margins = np.array([r["margin"] for r in results])

    for mech in mechanism_keys:
        firings_per_seed = np.array([r["firings"].get(mech, 0) for r in results])
        actions_per_seed = np.array([r["actions_changed"].get(mech, 0) for r in results])

        total_firings = int(np.sum(firings_per_seed))
        unique_seeds = int(np.sum(firings_per_seed > 0))
        pct_turns = float(total_firings / total_turns * 100.0)
        total_actions = int(np.sum(actions_per_seed))

        # Correlation with reward and margin
        if np.std(firings_per_seed) > 1e-6 and np.std(rewards) > 1e-6:
            corr_reward = float(np.corrcoef(firings_per_seed, rewards)[0, 1])
            corr_margin = float(np.corrcoef(firings_per_seed, margins)[0, 1])
        else:
            corr_reward = 0.0
            corr_margin = 0.0

        stats[mech] = {
            "total_firings": total_firings,
            "unique_seeds": unique_seeds,
            "unique_seeds_pct": float(unique_seeds / len(results) * 100.0),
            "pct_of_all_turns": pct_turns,
            "total_actions_changed": total_actions,
            "mean_actions_per_seed": float(np.mean(actions_per_seed)),
            "reward_correlation": corr_reward,
            "margin_correlation": corr_margin,
        }

    # Aggregate commodity breakdown for market preempt
    commodity_totals = defaultdict(int)
    for r in results:
        for item, count in r["commodity_firings"].items():
            commodity_totals[item] += count

    output = {
        "metadata": {
            "protocol": "V54++ Residual Mechanism Census",
            "fresh_seed_count": len(results),
            "seed_range": [seeds[0], seeds[-1]],
            "total_turns_analyzed": total_turns,
            "elapsed_seconds": total_time,
            "v54p_mean_reward": float(np.mean(rewards)),
            "v66_mean_reward": float(np.mean([r["reward_v66"] for r in results])),
            "v54p_mean_margin": float(np.mean(margins)),
            "v54p_win_rate": float(np.mean(margins > 0) * 100.0),
        },
        "census_statistics": stats,
        "preempt_commodities": dict(commodity_totals),
        "raw_results_sample": results[:10],
    }

    out_path = os.path.join(BASE_DIR, "research", "residual_census_500seeds.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Census results saved to {out_path}")
    print("\n--- RESIDUAL MECHANISM CENSUS (500 Fresh Seeds) ---")
    print(f"{'Mechanism':<24} | {'Firings':<8} | {'% Turns':<8} | {'Seeds':<7} | {'Actions':<8} | {'Corr(Reward)':<12}")
    print("-" * 78)
    for mech, s in sorted(stats.items(), key=lambda x: x[1]["total_firings"], reverse=True):
        print(
            f"{mech:<24} | {s['total_firings']:<8} | {s['pct_of_all_turns']:<7.2f}% | "
            f"{s['unique_seeds']:<7} | {s['total_actions_changed']:<8} | {s['reward_correlation']:<12.3f}"
        )

if __name__ == "__main__":
    main()
