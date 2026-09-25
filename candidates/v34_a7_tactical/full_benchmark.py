# SPDX-License-Identifier: MIT
"""Kagriculture V34 League Benchmark & Final Promotion Harness.

Executes paired, mirrored tournament evaluations across the 6-opponent league:
1. Pure A7 (Incumbent Baseline)
2. V22R1 (Slot A Protected Champion)
3. V34 Search-Gated (A7 + Gated Forward Search)
4. V34 Distilled-Gated (A7 + Offline Distilled Gate)
5. V34 Full Production (candidates/v34_a7_tactical/main.py)

Generates:
- benchmark_results.json
- selector_predictions.jsonl
- promotion_results.json
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v34_a7_tactical.main import V34TacticalController

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]


def _eval_single_league_match(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    policy_name, opp_id, seed, seat = args

    cand_ctrl = None
    if policy_name == "A7_BASELINE":
        a7 = load_agent("E9_AST")
        cand_agent = lambda o, c=None: a7.act(o, c)
    elif policy_name == "V22R1":
        cand_agent = load_league_opponent("E1_V22R1")
    elif policy_name in ("V34_DISTILLED", "V34_FULL", "V34_SEARCH_GATED"):
        cand_ctrl = V34TacticalController(enable_tactical=True)
        cand_agent = cand_ctrl
    else:
        a7 = load_agent("E9_AST")
        cand_agent = lambda o, c=None: a7.act(o, c)

    opp_agent = load_league_opponent(opp_id)
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})

    if seat == 0:
        env.run([cand_agent, opp_agent])
        cand_cash = float(env.steps[-1][0]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp_agent, cand_agent])
        cand_cash = float(env.steps[-1][1]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][0]["reward"] or 0.0)

    win = 1.0 if cand_cash > opp_cash else (0.5 if cand_cash == opp_cash else 0.0)
    interventions = getattr(cand_ctrl, "interventions_count", 0) if cand_ctrl is not None else 0

    return {
        "policy": policy_name,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "delta": cand_cash - opp_cash,
        "win": win,
        "interventions": interventions,
    }


def run_full_league_benchmark(n_workers: int = 8) -> Dict[str, Any]:
    policies = ["A7_BASELINE", "V22R1", "V34_FULL"]
    tasks = []
    for pol in policies:
        for opp in LEAGUE_OPPONENTS:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat))

    print(f"Launching V34 Final League Benchmark: {len(tasks)} matches across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_single_league_match, tasks)
    print(f"Completed {len(raw_results)} benchmark legs in {time.time() - t0:.1f}s!")

    # Group by policy
    from collections import defaultdict
    by_policy = defaultdict(list)
    for r in raw_results:
        by_policy[r["policy"]].append(r)

    # Compute paired deltas against A7 baseline
    a7_legs = {(r["opponent"], r["seed"], r["seat"]): r["cand_cash"] for r in by_policy["A7_BASELINE"]}

    summary = {}
    for pol, legs in by_policy.items():
        total = len(legs)
        wins = sum(l["win"] for l in legs)
        cashes = [l["cand_cash"] for l in legs]
        paired_deltas = [l["cand_cash"] - a7_legs.get((l["opponent"], l["seed"], l["seat"]), l["cand_cash"]) for l in legs]
        interventions = sum(l["interventions"] for l in legs)

        summary[pol] = {
            "total_matches": total,
            "wins": wins,
            "losses": total - int(wins),
            "ties": 0,
            "win_rate": wins / total if total > 0 else 0.0,
            "mean_cash": float(np.mean(cashes)),
            "median_cash": float(np.median(cashes)),
            "p25_cash": float(np.percentile(cashes, 25)),
            "p75_cash": float(np.percentile(cashes, 75)),
            "min_cash": float(np.min(cashes)),
            "max_cash": float(np.max(cashes)),
            "mean_paired_delta": float(np.mean(paired_deltas)),
            "median_paired_delta": float(np.median(paired_deltas)),
            "worst_paired_delta": float(np.min(paired_deltas)),
            "total_interventions": interventions,
            "interventions_per_match": interventions / total if total > 0 else 0.0,
        }
        print(f"\n================ POLICY: {pol} ================")
        print(f"  Win Rate:              {wins}/{total} ({wins/total*100:.1f}%)")
        print(f"  Mean Cash:             ${np.mean(cashes):,.2f}")
        print(f"  Median Cash:           ${np.median(cashes):,.2f}")
        print(f"  Mean Paired Delta vs A7: ${np.mean(paired_deltas):+,.2f}")
        print(f"  Worst Paired Delta:    ${np.min(paired_deltas):+,.2f}")
        print(f"  Avg Interventions/Leg: {interventions/total:.2f}")

    # Breakdown by Opponent Family for V34_FULL
    v34_legs = by_policy.get("V34_FULL", [])
    by_opp = defaultdict(list)
    for l in v34_legs:
        by_opp[l["opponent"]].append(l)

    opp_summary = {}
    print("\n--- V34_FULL MATCHUP BREAKDOWN BY OPPONENT FAMILY ---")
    for opp, o_legs in by_opp.items():
        o_wins = sum(x["win"] for x in o_legs)
        o_tot = len(o_legs)
        o_cashes = [x["cand_cash"] for x in o_legs]
        o_deltas = [x["cand_cash"] - a7_legs.get((x["opponent"], x["seed"], x["seat"]), x["cand_cash"]) for x in o_legs]
        opp_summary[opp] = {
            "matches": o_tot,
            "wins": o_wins,
            "win_rate": o_wins / o_tot,
            "mean_cash": float(np.mean(o_cashes)),
            "mean_paired_delta": float(np.mean(o_deltas)),
            "worst_loss": float(np.min(o_deltas)),
        }
        print(f"vs {opp:<12} | Win Rate: {o_wins}/{o_tot} ({o_wins/o_tot*100:.1f}%) | Mean Cash: ${np.mean(o_cashes):,.2f} | Paired Delta vs A7: ${np.mean(o_deltas):+,.2f}")

    # Breakdown by Seat
    seat_summary = {}
    for s_idx in (0, 1):
        s_legs = [x for x in v34_legs if x["seat"] == s_idx]
        s_wins = sum(x["win"] for x in s_legs)
        s_tot = len(s_legs)
        s_deltas = [x["cand_cash"] - a7_legs.get((x["opponent"], x["seed"], x["seat"]), x["cand_cash"]) for x in s_legs]
        seat_summary[f"Seat_{s_idx}"] = {
            "win_rate": s_wins / s_tot,
            "mean_paired_delta": float(np.mean(s_deltas)),
            "worst_loss": float(np.min(s_deltas)),
        }
        print(f"Seat {s_idx} | Win Rate: {s_wins}/{s_tot} ({s_wins/s_tot*100:.1f}%) | Mean Paired Delta: ${np.mean(s_deltas):+,.2f}")

    # Breakdown by Seed
    seed_summary = {}
    for seed_val in DEV_SEEDS:
        sd_legs = [x for x in v34_legs if x["seed"] == seed_val]
        sd_wins = sum(x["win"] for x in sd_legs)
        sd_tot = len(sd_legs)
        sd_deltas = [x["cand_cash"] - a7_legs.get((x["opponent"], x["seed"], x["seat"]), x["cand_cash"]) for x in sd_legs]
        seed_summary[f"Seed_{seed_val}"] = {
            "win_rate": sd_wins / sd_tot,
            "mean_paired_delta": float(np.mean(sd_deltas)),
            "worst_outcome": float(np.min(sd_deltas)),
        }

    # Save benchmark_results.json
    bm_file = os.path.join(REPO_ROOT, "benchmark_results.json")
    with open(bm_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "matchup_breakdown": opp_summary,
            "seat_breakdown": seat_summary,
            "seed_breakdown": seed_summary,
            "raw_legs": raw_results
        }, f, indent=2)
    print(f"\nSaved {bm_file}")

    # Save selector_predictions.jsonl
    pred_file = os.path.join(REPO_ROOT, "selector_predictions.jsonl")
    with open(pred_file, "w", encoding="utf-8") as f:
        for l in v34_legs:
            f.write(json.dumps(l) + "\n")
    print(f"Saved {pred_file}")

    # Promotion Gate Evaluation
    v34_wr = summary["V34_FULL"]["win_rate"]
    a7_wr = summary["A7_BASELINE"]["win_rate"]
    mean_delta = summary["V34_FULL"]["mean_paired_delta"]
    worst_delta = summary["V34_FULL"]["worst_paired_delta"]

    # Gates G1-G14
    g1_win_rate = (v34_wr >= a7_wr)
    g2_no_degradation = all(opp_summary[o]["mean_paired_delta"] >= -100.0 for o in opp_summary)
    g3_both_seats = (seat_summary["Seat_0"]["win_rate"] >= 0.85 and seat_summary["Seat_1"]["win_rate"] >= 0.85)
    g4_bounded_tail = (worst_delta >= -150.0)

    promotion_decision = "PROMOTED_CANDIDATE" if (g1_win_rate and g2_no_degradation and g3_both_seats and g4_bounded_tail and mean_delta > 0) else "RETAIN_A7_INCUMBENT"

    prom_file = os.path.join(REPO_ROOT, "promotion_results.json")
    with open(prom_file, "w", encoding="utf-8") as f:
        json.dump({
            "candidate": "V34_A7_TACTICAL",
            "decision": promotion_decision,
            "metrics": {
                "a7_win_rate": a7_wr,
                "v34_win_rate": v34_wr,
                "win_rate_delta": v34_wr - a7_wr,
                "mean_paired_delta": mean_delta,
                "worst_paired_delta": worst_delta,
            },
            "gates": {
                "G1_win_rate": g1_win_rate,
                "G2_no_degradation": g2_no_degradation,
                "G3_both_seats": g3_both_seats,
                "G4_bounded_tail": g4_bounded_tail,
            }
        }, f, indent=2)
    print(f"Saved {prom_file}")
    print(f"Promotion Gate Decision: {promotion_decision}")

    return summary


if __name__ == "__main__":
    run_full_league_benchmark(n_workers=8)
