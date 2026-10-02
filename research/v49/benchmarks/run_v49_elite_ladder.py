#!/usr/bin/env python3
"""Comprehensive Elite Ladder Benchmark for Kagriculture V49 Meta Fusion.

Evaluates paired performance of V49 vs V48 across 6 elite opponents:
1. V44
2. dmitrii_lb2800
3. tetsutani_pasture
4. kaitofukami_v48_3009
5. indarkarhana_top10
6. saiteja_mega_3000

256 paired legs per opponent (128 seeds x 2 seats) = 1,536 paired legs (3,072 full games).
Saves to research/v49/benchmarks/final_ladder.json and research/v49/elite_results.json.
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
import candidates.v49_meta_fusion.main as v49_mod

SEEDS = [250400 + i for i in range(128)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def run_paired_match(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = args
    opp_seat = 1 - seat

    # 1. V48 vs Opponent
    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    opp1 = load_elite_agent(opp_name)
    agent_v48 = v48_mod.agent
    for _ in range(719):
        a_v48 = agent_v48(obs1[seat])
        a_opp1 = opp1.act(obs1[opp_seat]) if hasattr(opp1, "act") else opp1(obs1[opp_seat])
        actions = [a_v48, a_opp1] if seat == 0 else [a_opp1, a_v48]
        obs1, _, _, _ = sim1.step(actions)
    cash_v48 = float(obs1[seat]["farms"][seat]["money"])
    cash_opp1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. V49 vs Opponent
    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    opp2 = load_elite_agent(opp_name)
    agent_v49 = v49_mod.agent
    for _ in range(719):
        a_v49 = agent_v49(obs2[seat])
        a_opp2 = opp2.act(obs2[opp_seat]) if hasattr(opp2, "act") else opp2(obs2[opp_seat])
        actions = [a_v49, a_opp2] if seat == 0 else [a_opp2, a_v49]
        obs2, _, _, _ = sim2.step(actions)
    cash_v49 = float(obs2[seat]["farms"][seat]["money"])
    cash_opp2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash_v48": cash_v48,
        "cash_v49": cash_v49,
        "delta": cash_v49 - cash_v48,
        "win_v48": cash_v48 > cash_opp1,
        "win_v49": cash_v49 > cash_opp2,
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

    print("=" * 80)
    print("V49 META FUSION COMPREHENSIVE ELITE LADDER BENCHMARK")
    print("=" * 80)
    print(f"Seeds: {len(SEEDS)} | Seats: 2 | Total Legs per Opponent: {len(SEEDS)*2}\n")

    ladder_summary = {}

    for opp_name in opponents:
        print(f"--- Benchmarking V49 vs {opp_name} (256 paired legs) ---")
        tasks = [(s, seat, opp_name) for s in SEEDS for seat in (0, 1)]

        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(run_paired_match, tasks))

        deltas = [r["delta"] for r in results]
        wins_v48 = sum(r["win_v48"] for r in results)
        wins_v49 = sum(r["win_v49"] for r in results)
        rescues = sum(1 for r in results if not r["win_v48"] and r["win_v49"])
        casualties = sum(1 for r in results if r["win_v48"] and not r["win_v49"])
        active = [r for r in results if r["delta"] != 0.0]

        summary = {
            "legs": len(results),
            "win_rate_v48": float(wins_v48 / len(results)),
            "win_rate_v49": float(wins_v49 / len(results)),
            "mean_delta": float(np.mean(deltas)),
            "median_delta": float(np.median(deltas)),
            "ci_95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
            "p10_delta": float(np.percentile(deltas, 10.0)),
            "rescues": rescues,
            "casualties": casualties,
            "active_legs": len(active),
            "active_mean": float(np.mean([r["delta"] for r in active])) if active else 0.0,
            "active_median": float(np.median([r["delta"] for r in active])) if active else 0.0,
        }
        ladder_summary[opp_name] = summary

        print(f"  V49 Win Rate: {summary['win_rate_v49']*100:.1f}% (V48: {summary['win_rate_v48']*100:.1f}%)")
        print(f"  Overall Mean Delta vs V48: {summary['mean_delta']:+7.2f} (95% CI [{summary['ci_95'][0]:+7.2f}, {summary['ci_95'][1]:+7.2f}]), Median: {summary['median_delta']:+7.2f}")
        if active:
            print(f"  Active Cohort ({len(active)} legs): Mean Delta: {summary['active_mean']:+7.2f}, Median: {summary['active_median']:+7.2f}")
        print(f"  Rescues (Loss -> Win): {rescues} | Casualties (Win -> Loss): {casualties}\n")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "benchmarks", "final_ladder.json")
    with open(out_file, "w") as f:
        json.dump(ladder_summary, f, indent=2)

    elite_file = os.path.join(REPO_ROOT, "research", "v49", "elite_results.json")
    with open(elite_file, "w") as f:
        json.dump(ladder_summary, f, indent=2)

    print(f"Final Ladder results saved to {out_file} and {elite_file}!")


if __name__ == "__main__":
    main()
