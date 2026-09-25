# SPDX-License-Identifier: MIT
"""Kagriculture V35 Expanded Validation Benchmark & Statistical Bootstrap.

Executes a large-scale paired tournament benchmark across:
- 10 Development Seeds:
  Dev Cohort: 249675, 249676, 249677, 249678, 249679
  Fresh Cohort: 249680, 249681, 249682, 249683, 249684
- 6 League Opponents: E2_A7, E1_V22R1, E0_V3, E8_DMITRII, V54, SYN_AGG
- 2 Seats: Seat 0, Seat 1
Total: 120 paired legs (240 full tournament matches).

Computes:
- Win rate, mean cash, median cash, paired cash delta, worst cash delta
- Rescued A7 losses, preserved A7 wins, casualty count
- 1,000-sample paired bootstrap confidence intervals (P2.5, P50, P97.5)
- Promotion gate verdicts (G1..G7)
Outputs benchmark_results.json and promotion_results.json.
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v35_a7_opening.main import V35OpeningController

VALIDATION_SEEDS = [
    249675, 249676, 249677, 249678, 249679,  # Dev Cohort
    249680, 249681, 249682, 249683, 249684   # Fresh Cohort
]


def _eval_validation_leg(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    policy_name, opp_id, seed, seat = args

    cand_ctrl = None
    if policy_name == "A7_BASELINE":
        a7 = load_agent("E9_AST")
        cand_agent = lambda o, c=None: a7.act(o, c)
    elif policy_name == "V35_FULL":
        cand_ctrl = V35OpeningController(wash_buy=25, wash_sell=25)
        cand_agent = cand_ctrl
    else:
        raise ValueError(f"Unknown policy {policy_name}")

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


def paired_bootstrap(
    a7_legs: List[Dict[str, Any]],
    cand_legs: List[Dict[str, Any]],
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(a7_legs)

    wr_deltas = []
    cash_deltas = []

    for _ in range(n_bootstraps):
        idx = rng.integers(0, n, size=n)
        boot_a7_wins = sum(a7_legs[i]["win"] for i in idx)
        boot_cand_wins = sum(cand_legs[i]["win"] for i in idx)
        wr_deltas.append((boot_cand_wins - boot_a7_wins) / n)

        boot_deltas = [cand_legs[i]["cand_cash"] - a7_legs[i]["cand_cash"] for i in idx]
        cash_deltas.append(np.mean(boot_deltas))

    return {
        "win_rate_delta": {
            "mean": float(np.mean(wr_deltas)),
            "median": float(np.median(wr_deltas)),
            "ci_95_lower": float(np.percentile(wr_deltas, 2.5)),
            "ci_95_upper": float(np.percentile(wr_deltas, 97.5)),
        },
        "mean_paired_cash_delta": {
            "mean": float(np.mean(cash_deltas)),
            "median": float(np.median(cash_deltas)),
            "ci_95_lower": float(np.percentile(cash_deltas, 2.5)),
            "ci_95_upper": float(np.percentile(cash_deltas, 97.5)),
        },
    }


def run_expanded_validation(n_workers: int = 8) -> Dict[str, Any]:
    tasks = []
    for pol in ["A7_BASELINE", "V35_FULL"]:
        for opp in LEAGUE_OPPONENTS:
            for s in VALIDATION_SEEDS:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat))

    print(f"Executing V35 Expanded Validation Benchmark: {len(tasks)} matches ({len(VALIDATION_SEEDS)} seeds x 6 opps x 2 seats x 2 policies) across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_validation_leg, tasks)
    elapsed = time.time() - t0
    print(f"Expanded benchmark completed in {elapsed:.1f}s.")

    by_policy: Dict[str, List[Dict[str, Any]]] = {"A7_BASELINE": [], "V35_FULL": []}
    for r in raw_results:
        by_policy[r["policy"]].append(r)

    a7_lookup = {(r["opponent"], r["seed"], r["seat"]): r for r in by_policy["A7_BASELINE"]}

    summary = {}
    for pol in ["A7_BASELINE", "V35_FULL"]:
        legs = by_policy[pol]
        tot = len(legs)
        wins = sum(x["win"] for x in legs)
        cashes = [x["cand_cash"] for x in legs]
        paired_deltas = [
            x["cand_cash"] - a7_lookup[(x["opponent"], x["seed"], x["seat"])]["cand_cash"]
            for x in legs
        ]
        interventions = sum(x["interventions"] for x in legs)

        summary[pol] = {
            "total_matches": tot,
            "wins": wins,
            "losses": tot - int(wins),
            "ties": sum(1 for x in legs if x["win"] == 0.5),
            "win_rate": wins / tot if tot > 0 else 0.0,
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
            "interventions_per_match": interventions / tot if tot > 0 else 0.0,
        }

    # Matchup breakdown by opponent family
    opp_summary = {}
    v35_legs = by_policy["V35_FULL"]
    a7_ordered = [a7_lookup[(x["opponent"], x["seed"], x["seat"])] for x in v35_legs]

    for opp in LEAGUE_OPPONENTS:
        o_v35 = [x for x in v35_legs if x["opponent"] == opp]
        o_a7 = [a7_lookup[(x["opponent"], x["seed"], x["seat"])] for x in o_v35]
        o_tot = len(o_v35)
        o_v35_wins = sum(x["win"] for x in o_v35)
        o_a7_wins = sum(x["win"] for x in o_a7)
        o_deltas = [x["cand_cash"] - y["cand_cash"] for x, y in zip(o_v35, o_a7)]

        rescued = sum(1 for x, y in zip(o_v35, o_a7) if y["win"] < 1.0 and x["win"] == 1.0)
        casualty = sum(1 for x, y in zip(o_v35, o_a7) if y["win"] == 1.0 and x["win"] < 1.0)

        opp_summary[opp] = {
            "matches": o_tot,
            "a7_wins": o_a7_wins,
            "v35_wins": o_v35_wins,
            "a7_win_rate": o_a7_wins / o_tot,
            "v35_win_rate": o_v35_wins / o_tot,
            "mean_paired_delta": float(np.mean(o_deltas)),
            "worst_paired_delta": float(np.min(o_deltas)),
            "rescued_losses": rescued,
            "casualty_wins": casualty,
        }

    # Seat breakdown
    seat_summary = {}
    for s_idx in (0, 1):
        s_v35 = [x for x in v35_legs if x["seat"] == s_idx]
        s_a7 = [a7_lookup[(x["opponent"], x["seed"], x["seat"])] for x in s_v35]
        s_tot = len(s_v35)
        s_wins = sum(x["win"] for x in s_v35)
        s_deltas = [x["cand_cash"] - y["cand_cash"] for x, y in zip(s_v35, s_a7)]

        seat_summary[f"Seat_{s_idx}"] = {
            "matches": s_tot,
            "win_rate": s_wins / s_tot,
            "mean_paired_delta": float(np.mean(s_deltas)),
            "worst_loss": float(np.min(s_deltas)),
        }

    # Seed breakdown (dev vs fresh cohort)
    seed_summary = {}
    for sd in VALIDATION_SEEDS:
        sd_v35 = [x for x in v35_legs if x["seed"] == sd]
        sd_a7 = [a7_lookup[(x["opponent"], x["seed"], x["seat"])] for x in sd_v35]
        sd_tot = len(sd_v35)
        sd_wins = sum(x["win"] for x in sd_v35)
        sd_a7_wins = sum(x["win"] for x in sd_a7)
        sd_deltas = [x["cand_cash"] - y["cand_cash"] for x, y in zip(sd_v35, sd_a7)]

        seed_summary[f"Seed_{sd}"] = {
            "cohort": "DEV" if sd in VALIDATION_SEEDS[:5] else "FRESH",
            "matches": sd_tot,
            "a7_wins": sd_a7_wins,
            "v35_wins": sd_wins,
            "v35_win_rate": sd_wins / sd_tot,
            "mean_paired_delta": float(np.mean(sd_deltas)),
            "rescued_losses": sum(1 for x, y in zip(sd_v35, sd_a7) if y["win"] < 1.0 and x["win"] == 1.0),
            "casualty_wins": sum(1 for x, y in zip(sd_v35, sd_a7) if y["win"] == 1.0 and x["win"] < 1.0),
        }

    # Bootstrap
    bs_results = paired_bootstrap(a7_ordered, v35_legs, n_bootstraps=1000)

    # Save benchmark_results.json
    bm_file = os.path.join(REPO_ROOT, "benchmark_results.json")
    with open(bm_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "matchup_breakdown": opp_summary,
            "seat_breakdown": seat_summary,
            "seed_breakdown": seed_summary,
            "bootstrap_analysis": bs_results,
            "raw_legs": raw_results,
        }, f, indent=2)
    print(f"Saved {bm_file}")

    # Promotion Gate Evaluation
    v35_wr = summary["V35_FULL"]["win_rate"]
    a7_wr = summary["A7_BASELINE"]["win_rate"]
    mean_delta = summary["V35_FULL"]["mean_paired_delta"]
    worst_delta = summary["V35_FULL"]["worst_paired_delta"]
    total_rescued = sum(opp_summary[o]["rescued_losses"] for o in opp_summary)
    total_casualties = sum(opp_summary[o]["casualty_wins"] for o in opp_summary)

    g1_win_rate = (v35_wr >= a7_wr)
    g2_no_degradation = all(opp_summary[o]["mean_paired_delta"] >= -50.0 for o in opp_summary)
    g3_both_seats = (seat_summary["Seat_0"]["win_rate"] >= 0.85 and seat_summary["Seat_1"]["win_rate"] >= 0.85)
    g4_bounded_tail = (worst_delta >= -100.0)
    g5_zero_casualties = (total_casualties == 0)
    g6_positive_rescues = (total_rescued > 0)
    g7_bootstrap_positive = (bs_results["win_rate_delta"]["ci_95_lower"] >= 0.0)

    all_gates_passed = all([
        g1_win_rate, g2_no_degradation, g3_both_seats, g4_bounded_tail,
        g5_zero_casualties, g6_positive_rescues, g7_bootstrap_positive
    ])

    promotion_decision = "PROMOTED_CANDIDATE" if all_gates_passed else "RETAIN_A7_INCUMBENT"

    prom_file = os.path.join(REPO_ROOT, "promotion_results.json")
    with open(prom_file, "w", encoding="utf-8") as f:
        json.dump({
            "candidate": "V35_A7_OPENING",
            "decision": promotion_decision,
            "metrics": {
                "a7_win_rate": a7_wr,
                "v35_win_rate": v35_wr,
                "win_rate_delta": v35_wr - a7_wr,
                "mean_paired_delta": mean_delta,
                "worst_paired_delta": worst_delta,
                "total_rescued": total_rescued,
                "total_casualties": total_casualties,
            },
            "bootstrap": bs_results,
            "gates": {
                "G1_win_rate_superiority": g1_win_rate,
                "G2_no_opponent_degradation": g2_no_degradation,
                "G3_both_seats_robustness": g3_both_seats,
                "G4_bounded_tail_risk": g4_bounded_tail,
                "G5_zero_casualties": g5_zero_casualties,
                "G6_positive_rescues": g6_positive_rescues,
                "G7_bootstrap_confidence_positive": g7_bootstrap_positive,
            }
        }, f, indent=2)
    print(f"Saved {prom_file}")
    print(f"Final Promotion Gate Decision: {promotion_decision}")

    return summary


if __name__ == "__main__":
    run_expanded_validation(n_workers=8)
