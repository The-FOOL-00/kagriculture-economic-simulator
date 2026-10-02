#!/usr/bin/env python3
"""Comprehensive Elite Ladder & Benchmark for Kagriculture V48 Challenger.

Evaluates candidates/v48_challenger/main.py against:
1. B1: thomastschinkel_2945 (Primary anchor - direct head-to-head across 256 paired legs)
2. B0: V44 (Incumbent baseline)
3. Elite Suite:
   - kaitofukami_v48_3009
   - indarkarhana_top10
   - tetsutani_pasture
   - dmitrii_lb2800
   - saiteja_mega_3000

Measures:
- Head-to-head win rate, margin, cash alpha
- Casualties (2945 Win -> V48 Loss)
- Rescues (2945 Loss -> V48 Win)
- 95% Confidence Interval
- P10, median
Saves to research/v48/benchmarks/final_ladder.json and research/v48/elite/elite_results.json.
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v48_challenger.main as v48_mod
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945

# 128 Clean dev seeds
SEEDS = [249800 + i for i in range(128)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def run_paired_leg(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = args
    opp_seat = 1 - seat

    # 1. 2945 Baseline vs Opponent
    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    agent_2945 = m2945.agent
    opp1 = load_elite_agent(opp_name)
    for _ in range(719):
        a_2945 = agent_2945(obs1[seat])
        a_opp1 = opp1.act(obs1[opp_seat]) if hasattr(opp1, "act") else opp1(obs1[opp_seat])
        actions = [a_2945, a_opp1] if seat == 0 else [a_opp1, a_2945]
        obs1, _, _, _ = sim1.step(actions)
    cash_2945 = float(obs1[seat]["farms"][seat]["money"])
    cash_opp1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. V48 Challenger vs Opponent
    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    agent_v48 = v48_mod.agent
    opp2 = load_elite_agent(opp_name)
    for _ in range(719):
        a_v48 = agent_v48(obs2[seat])
        a_opp2 = opp2.act(obs2[opp_seat]) if hasattr(opp2, "act") else opp2(obs2[opp_seat])
        actions = [a_v48, a_opp2] if seat == 0 else [a_opp2, a_v48]
        obs2, _, _, _ = sim2.step(actions)
    cash_v48 = float(obs2[seat]["farms"][seat]["money"])
    cash_opp2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    town = obs1[0].get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])
    first_two = tuple(shops[:2])
    is_active = first_two in v48_mod._V48_OVERRIDES

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "shops": shops,
        "is_active": is_active,
        "cash_2945": cash_2945,
        "cash_v48": cash_v48,
        "delta": cash_v48 - cash_2945,
        "win_2945": cash_2945 > cash_opp1,
        "win_v48": cash_v48 > cash_opp2,
        "margin_2945": cash_2945 - cash_opp1,
        "margin_v48": cash_v48 - cash_opp2,
    }


def main():
    opponents = [
        "V44",
        "dmitrii_lb2800",
        "tetsutani_pasture",
        "kaitofukami_v48_3009",
        "indarkarhana_top10",
        "saiteja_mega_3000",
    ]

    print("================================================================================")
    print("V48 CHALLENGER COMPREHENSIVE ELITE LADDER BENCHMARK")
    print("================================================================================")
    print(f"Seeds: {len(SEEDS)} | Seats: 2 | Total Legs per Opponent: {len(SEEDS) * 2}")

    ladder_summary = {}

    for opp in opponents:
        print(f"\n--- Benchmarking V48 vs {opp} (256 paired legs) ---")
        tasks = [(s, seat, opp) for s in SEEDS for seat in (0, 1)]

        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(run_paired_leg, tasks))

        deltas = [r["delta"] for r in results]
        wins_2945 = sum(r["win_2945"] for r in results)
        wins_v48 = sum(r["win_v48"] for r in results)
        rescues = sum(not r["win_2945"] and r["win_v48"] for r in results)
        casualties = sum(r["win_2945"] and not r["win_v48"] for r in results)

        mean_d = float(np.mean(deltas))
        median_d = float(np.median(deltas))
        std_err = float(np.std(deltas, ddof=1) / np.sqrt(len(deltas)))
        ci_low = mean_d - 1.96 * std_err
        ci_high = mean_d + 1.96 * std_err
        p10_d = float(np.percentile(deltas, 10))

        active_results = [r for r in results if r["is_active"]]
        active_deltas = [r["delta"] for r in active_results]
        active_mean = float(np.mean(active_deltas)) if active_deltas else 0.0
        active_median = float(np.median(active_deltas)) if active_deltas else 0.0

        ladder_summary[opp] = {
            "legs": len(results),
            "win_rate_2945": float(wins_2945 / len(results)),
            "win_rate_v48": float(wins_v48 / len(results)),
            "mean_delta": mean_d,
            "median_delta": median_d,
            "ci_95": [ci_low, ci_high],
            "p10_delta": p10_d,
            "rescues": rescues,
            "casualties": casualties,
            "active_legs": len(active_results),
            "active_mean": active_mean,
            "active_median": active_median,
        }

        print(f"  V48 Win Rate: {wins_v48/len(results)*100:.1f}% (2945: {wins_2945/len(results)*100:.1f}%)")
        print(f"  Overall Mean Delta vs 2945: {mean_d:+7.2f} (95% CI [{ci_low:+7.2f}, {ci_high:+7.2f}]), Median: {median_d:+7.2f}")
        print(f"  Active Cohort ({len(active_results)} legs): Mean Delta: {active_mean:+7.2f}, Median: {active_median:+7.2f}")
        print(f"  Rescues (Loss -> Win): {rescues} | Casualties (Win -> Loss): {casualties}")

    ladder_path = os.path.join(REPO_ROOT, "research", "v48", "benchmarks", "final_ladder.json")
    with open(ladder_path, "w") as f:
        json.dump(ladder_summary, f, indent=2)

    elite_path = os.path.join(REPO_ROOT, "research", "v48", "elite", "elite_results.json")
    with open(elite_path, "w") as f:
        json.dump(ladder_summary, f, indent=2)

    print(f"\nFinal Ladder results saved to {ladder_path} and {elite_path}!")


if __name__ == "__main__":
    main()
