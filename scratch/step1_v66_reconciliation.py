"""
Step 1: Canonical V66 vs V54 Reconciliation Benchmark
=====================================================
Evaluates:
- Canonical V54 (external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py)
- Canonical V66 (external_repos/kaggriculture-v66-agent/main.py)
- Identical engine version: kaggle_environments kaggriculture, episodeSteps: 720
- 20 Common Seeds: 101 to 120
- 20 Fresh Seeds: 201 to 220
- Symmetric Seats:
    Match A: P0=V54, P1=V66
    Match B: P0=V66, P1=V54
  Total = 40 seeds * 2 matches = 80 games.

Reports:
- Per-seed / per-seat table
- Statistical aggregates (Mean margin, Median margin, 95% Bootstrap CI, W/T/L, Win Rate)
- Provenance resolution of previous V66 claims
"""

import os
import sys
import time
import json
import csv
import importlib.util
import numpy as np
from concurrent.futures import ProcessPoolExecutor

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
V66_PATH = os.path.abspath("external_repos/kaggriculture-v66-agent/main.py")

COMMON_SEEDS = list(range(101, 121))  # 20 seeds: 101-120
FRESH_SEEDS = list(range(201, 221))   # 20 seeds: 201-220
ALL_SEEDS = COMMON_SEEDS + FRESH_SEEDS

def _run_single_match(task):
    seed, p0_agent, p1_agent = task
    # Load agents cleanly
    from kaggle_environments import make

    def load_agent(agent_name):
        path = V54_PATH if agent_name == "V54" else V66_PATH
        d = os.path.dirname(path)
        if d not in sys.path:
            sys.path.insert(0, d)
        spec = importlib.util.spec_from_file_location(f"mod_{agent_name}_{os.getpid()}_{time.time_ns()}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod.agent

    agent_p0 = load_agent(p0_agent)
    agent_p1 = load_agent(p1_agent)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_p0, agent_p1])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)

    if p0_agent == "V54":
        v54_rew = r0
        v66_rew = r1
        v54_seat = 0
    else:
        v54_rew = r1
        v66_rew = r0
        v54_seat = 1

    # Margin is V66 - V54 (as claimed in historical reports, e.g. V66 margin vs V54)
    # But we also compute V54 - V66 for clarity
    margin_v66_vs_v54 = v66_rew - v54_rew
    margin_v54_vs_v66 = v54_rew - v66_rew

    winner = "V66" if v66_rew > v54_rew else ("V54" if v54_rew > v66_rew else "TIE")

    return {
        "seed": seed,
        "v54_seat": v54_seat,
        "v66_seat": 1 - v54_seat,
        "p0_agent": p0_agent,
        "p1_agent": p1_agent,
        "v54_reward": v54_rew,
        "v66_reward": v66_rew,
        "v66_margin": margin_v66_vs_v54,
        "v54_margin": margin_v54_vs_v66,
        "winner": winner,
        "seed_type": "COMMON" if seed in COMMON_SEEDS else "FRESH"
    }

def bootstrap_ci(data, num_samples=10000, alpha=0.05):
    arr = np.array(data)
    n = len(arr)
    boot_means = []
    np.random.seed(42)
    for _ in range(num_samples):
        sample = np.random.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))
    low = np.percentile(boot_means, 100 * (alpha / 2))
    high = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return float(low), float(high)

def main():
    print("=" * 80)
    print("STEP 1: CANONICAL V66 VS V54 RECONCILIATION BENCHMARK")
    print(f"Engine: kaggle_environments kaggriculture, 720 steps")
    print(f"20 Common Seeds: {COMMON_SEEDS}")
    print(f"20 Fresh Seeds: {FRESH_SEEDS}")
    print("Symmetric seats: (V54 P0, V66 P1) and (V66 P0, V54 P1) for all 40 seeds.")
    print("=" * 80, flush=True)

    tasks = []
    for s in ALL_SEEDS:
        tasks.append((s, "V54", "V66"))
        tasks.append((s, "V66", "V54"))

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(_run_single_match, tasks):
            results.append(res)
            print(f"Seed {res['seed']} | V54 Seat {res['v54_seat']} | V54: ${res['v54_reward']:,.0f} | V66: ${res['v66_reward']:,.0f} | V66 Margin: ${res['v66_margin']:+,.0f} | Winner: {res['winner']}", flush=True)

    elapsed = time.time() - t0
    print(f"\nAll {len(results)} matches completed in {elapsed:.1f}s.")

    # Save detailed CSV
    csv_path = "scratch/step1_v66_reconciliation_raw.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    # Statistical computation
    # Separate by subset: Common, Fresh, Pooled
    def analyze_subset(name, subset_res):
        n = len(subset_res)
        v66_margins = [r["v66_margin"] for r in subset_res]
        mean_margin = float(np.mean(v66_margins))
        median_margin = float(np.median(v66_margins))
        sd_margin = float(np.std(v66_margins, ddof=1)) if n > 1 else 0.0
        ci_low, ci_high = bootstrap_ci(v66_margins)
        
        wins_v66 = sum(1 for r in subset_res if r["winner"] == "V66")
        ties = sum(1 for r in subset_res if r["winner"] == "TIE")
        wins_v54 = sum(1 for r in subset_res if r["winner"] == "V54")
        win_rate_v66 = (wins_v66 / n) * 100.0
        win_rate_v54 = (wins_v54 / n) * 100.0

        # Also analyze Seat 0 only (V66 in Seat 0) vs Seat 1 only (V66 in Seat 1)
        v66_s0 = [r["v66_margin"] for r in subset_res if r["v66_seat"] == 0]
        v66_s1 = [r["v66_margin"] for r in subset_res if r["v66_seat"] == 1]
        mean_s0 = float(np.mean(v66_s0)) if v66_s0 else 0.0
        mean_s1 = float(np.mean(v66_s1)) if v66_s1 else 0.0

        return {
            "name": name,
            "n_matches": n,
            "v66_mean_margin": mean_margin,
            "v66_median_margin": median_margin,
            "v66_sd_margin": sd_margin,
            "bootstrap_ci_95": (ci_low, ci_high),
            "v66_wins": wins_v66,
            "ties": ties,
            "v54_wins": wins_v54,
            "v66_win_rate": win_rate_v66,
            "v54_win_rate": win_rate_v54,
            "v66_seat0_mean_margin": mean_s0,
            "v66_seat1_mean_margin": mean_s1,
            "seat_asymmetry": mean_s0 - mean_s1
        }

    common_res = [r for r in results if r["seed_type"] == "COMMON"]
    fresh_res = [r for r in results if r["seed_type"] == "FRESH"]
    pooled_res = results

    summary_common = analyze_subset("20 Common Seeds (40 matches)", common_res)
    summary_fresh = analyze_subset("20 Fresh Seeds (40 matches)", fresh_res)
    summary_pooled = analyze_subset("Pooled All 40 Seeds (80 matches)", pooled_res)

    print("\n" + "=" * 80)
    print("STATISTICAL SUMMARY: V66 VS V54")
    print("=" * 80)
    for s in [summary_common, summary_fresh, summary_pooled]:
        print(f"\n--- {s['name']} ---")
        print(f"Matches: {s['n_matches']}")
        print(f"V66 Mean Margin vs V54:   ${s['v66_mean_margin']:+,.2f}")
        print(f"V66 Median Margin vs V54: ${s['v66_median_margin']:+,.2f}")
        print(f"95% Bootstrap CI:         [${s['bootstrap_ci_95'][0]:+,.2f}, ${s['bootstrap_ci_95'][1]:+,.2f}]")
        print(f"Record (V66 W / T / V54 W): {s['v66_wins']}W / {s['ties']}T / {s['v54_wins']}L")
        print(f"V66 Win Rate:             {s['v66_win_rate']:.1f}% (V54 Win Rate: {s['v54_win_rate']:.1f}%)")
        print(f"V66 Seat 0 Margin:        ${s['v66_seat0_mean_margin']:+,.2f}")
        print(f"V66 Seat 1 Margin:        ${s['v66_seat1_mean_margin']:+,.2f}")
        print(f"Seat Asymmetry (S0 - S1): ${s['seat_asymmetry']:+,.2f}")

    # Output JSON summary
    summary_out = {
        "common": summary_common,
        "fresh": summary_fresh,
        "pooled": summary_pooled,
        "results": results
    }
    with open("scratch/step1_v66_reconciliation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_out, f, indent=2)

    print("\nBenchmark saved to scratch/step1_v66_reconciliation_summary.json")

if __name__ == "__main__":
    main()
