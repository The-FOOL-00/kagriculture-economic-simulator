#!/usr/bin/env python3
"""Revalidate V49 on Current Engine (V53 Section 3).

Runs V49 against 7 elite opponents: V48, V44, dmitrii, tetsutani, Kaito, indarkarhana, saiteja
across 32 fresh seeds [250600..250631] x 2 seats (448 total matches).
Establishes the canonical current-engine baseline reference for all V53 experiments.
"""

import concurrent.futures
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod
import candidates.v44_economic_portfolio.main as v44_mod

FRESH_SEEDS = [250600 + i for i in range(32)]
OPPONENTS = [
    "V48",
    "V44",
    "dmitrii_lb2800",
    "tetsutani_pasture",
    "kaitofukami_v48_3009",
    "indarkarhana_top10",
    "saiteja_mega_3000",
]


def load_opp(opp_name: str) -> Any:
    if opp_name == "V48":
        return v48_mod.agent
    elif opp_name == "V44":
        return v44_mod.agent
    else:
        return load_elite_agent(opp_name)


def run_v49_baseline_leg(task: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = task
    opp_seat = 1 - seat
    
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    agent = v49_mod.agent
    opp = load_opp(opp_name)

    for step in range(719):
        a_cand = agent(obs[seat])
        a_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    cash49 = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    delta = cash49 - cash_opp
    win = cash49 > cash_opp
    loss = cash49 < cash_opp
    tie = cash49 == cash_opp

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash49": cash49,
        "cash_opp": cash_opp,
        "delta": delta,
        "win": win,
        "loss": loss,
        "tie": tie,
    }


def compute_stats(deltas: np.ndarray) -> Dict[str, float]:
    rng = np.random.default_rng(42)
    boot_means = np.mean(rng.choice(deltas, size=(10000, len(deltas)), replace=True), axis=1)
    return {
        "mean": float(np.mean(deltas)),
        "median": float(np.median(deltas)),
        "p10": float(np.percentile(deltas, 10.0)),
        "ci95_low": float(np.percentile(boot_means, 2.5)),
        "ci95_high": float(np.percentile(boot_means, 97.5)),
    }


def main():
    print("=" * 80)
    print("V53 SECTION 3: REVALIDATE V49 BASELINE ON CURRENT ENGINE")
    print("=" * 80)

    tasks = [(s, seat, opp) for opp in OPPONENTS for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"Executing {len(tasks)} matches ({len(OPPONENTS)} opponents x 32 seeds x 2 seats)...")
    
    t0 = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_v49_baseline_leg, tasks))
    elapsed = time.time() - t0
    print(f"Completed all {len(results)} matches in {elapsed:.2f}s!")

    all_deltas = np.array([r["delta"] for r in results])
    overall_stats = compute_stats(all_deltas)
    
    wins = sum(r["win"] for r in results)
    losses = sum(r["loss"] for r in results)
    ties = sum(r["tie"] for r in results)
    total = len(results)

    per_opp = {}
    for opp in OPPONENTS:
        sub = [r for r in results if r["opp"] == opp]
        sub_d = np.array([r["delta"] for r in sub])
        stats = compute_stats(sub_d)
        w = sum(r["win"] for r in sub)
        l = sum(r["loss"] for r in sub)
        t = sum(r["tie"] for r in sub)
        per_opp[opp] = {
            "legs": len(sub),
            "wins": w,
            "losses": l,
            "ties": t,
            "win_rate": w / len(sub),
            "stats": stats,
            "seat0": {
                "mean_delta": float(np.mean([r["delta"] for r in sub if r["seat"] == 0])),
                "win_rate": sum(r["win"] for r in sub if r["seat"] == 0) / (len(sub) // 2),
            },
            "seat1": {
                "mean_delta": float(np.mean([r["delta"] for r in sub if r["seat"] == 1])),
                "win_rate": sum(r["win"] for r in sub if r["seat"] == 1) / (len(sub) // 2),
            }
        }
        print(f"  vs {opp:20s}: WR={w/len(sub)*100:5.2f}% ({w}/{len(sub)}) | Mean Delta={stats['mean']:+9.1f} | 95% CI=[{stats['ci95_low']:+9.1f}, {stats['ci95_high']:+9.1f}]")

    summary = {
        "engine": "kaggle_environments 1.32.7",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_legs": total,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / total,
        "overall_stats": overall_stats,
        "per_opponent": per_opp,
        "elapsed_seconds": elapsed,
    }

    out_json = os.path.join(REPO_ROOT, "research", "v53", "benchmarks", "v49_current_engine_baseline.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved current-engine baseline profile to {out_json}")


if __name__ == "__main__":
    main()
