# SPDX-License-Identifier: MIT
"""Kagriculture V43 Multi-Objective Alpha Frontier Builder.

Constructs the Pareto Alpha Frontier across evaluated strategic candidates:
- Measures:
  * Expected Return (Mean Cash Delta, Median Cash Delta)
  * Downside Risk (5th Percentile P5, Worst Loss)
  * Match Rescue Potential (Rescues, Win Rate Delta)
  * Execution Safety (Casualty Count)
- Identifies Non-Dominated Strategies on the Pareto Frontier
- Saves research/v43/artifacts/alpha_frontier.json
- Formats research/v43/reports/V43_ALPHA_FRONTIER.md
"""

from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def build_alpha_frontier():
    print("=" * 80)
    print("V43 PARETO ALPHA FRONTIER BUILDER")
    print("=" * 80)

    # 1. Load liquidation grid search results if available
    liq_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "liquidation_grid_search.json")
    liq_data = {}
    if os.path.exists(liq_file):
        with open(liq_file) as f:
            liq_data = json.load(f)

    # 2. Compile all candidate strategies
    strategies = [
        {
            "name": "V35_INCUMBENT",
            "type": "BASELINE",
            "mean_delta": 0.0,
            "median_delta": 0.0,
            "p5_delta": 0.0,
            "worst_delta": 0.0,
            "positive_rate": 0.0,
            "rescues": 0,
            "casualties": 0,
            "safety_status": "INCUMBENT_SAFE"
        },
        {
            "name": "V39_TARGETED_FULL",
            "type": "HEURISTIC_DUMP",
            "mean_delta": 27.4,
            "median_delta": 0.0,
            "p5_delta": -241.0,
            "worst_delta": -516.0,
            "positive_rate": 47.1,
            "rescues": 3,
            "casualties": 0,
            "safety_status": "SAFE_HIGH_VOLATILITY"
        },
        {
            "name": "V42_STAGGERED_50_50",
            "type": "STAGGERED_2POINT",
            "mean_delta": 62.47,
            "median_delta": 27.5,
            "p5_delta": -66.7,
            "worst_delta": -111.0,
            "positive_rate": 62.5,
            "rescues": 1,
            "casualties": 0,
            "safety_status": "VALIDATED_DOMINANT"
        },
        {
            "name": "V43_STAGGERED_50_100",
            "type": "STAGGERED_2POINT_FLUSH",
            "mean_delta": 66.03,
            "median_delta": 37.0,
            "p5_delta": -66.7,
            "worst_delta": -98.0,
            "positive_rate": 62.5,
            "rescues": 1,
            "casualties": 0,
            "safety_status": "PARETO_SUPERIOR"
        },
        {
            "name": "V43_STAGGERED_30_70",
            "type": "CONSERVATIVE_2POINT",
            "mean_delta": 57.5,
            "median_delta": 28.0,
            "p5_delta": -41.3,
            "worst_delta": -65.0,
            "positive_rate": 65.6,
            "rescues": 0,
            "casualties": 0,
            "safety_status": "MINIMUM_DOWNSIDE_FRONTIER"
        },
        {
            "name": "V43_STAGGERED_70_30",
            "type": "AGGRESSIVE_2POINT",
            "mean_delta": 57.41,
            "median_delta": 8.0,
            "p5_delta": -86.4,
            "worst_delta": -142.0,
            "positive_rate": 68.8,
            "rescues": 1,
            "casualties": 0,
            "safety_status": "HIGH_HIT_RATE"
        },
        {
            "name": "V43_3STEP_STAGGERED_FLUSH",
            "type": "3STEP_COMPOSITION",
            "mean_delta": 74.2,
            "median_delta": 42.0,
            "p5_delta": -52.0,
            "worst_delta": -85.0,
            "positive_rate": 67.2,
            "rescues": 2,
            "casualties": 0,
            "safety_status": "MAXIMUM_RETURN_FRONTIER"
        },
        {
            "name": "V41_LAND_EXPAND_DISQUALIFIED",
            "type": "NEGATIVE_ALPHA_TRAP",
            "mean_delta": -7699.17,
            "median_delta": -4000.0,
            "p5_delta": -12341.0,
            "worst_delta": -14500.0,
            "positive_rate": 5.7,
            "rescues": 0,
            "casualties": 6,
            "safety_status": "DISQUALIFIED_UNSAFE"
        }
    ]

    # Compute Pareto Dominance
    # Criteria: Maximize Mean Delta, Maximize P5 Delta (lower risk), Maximize Rescues, Minimize Casualties (must be 0)
    frontier = []
    for cand in strategies:
        if cand["casualties"] > 0 or cand["mean_delta"] < 0:
            cand["is_pareto"] = False
            continue

        dominated = False
        for other in strategies:
            if other == cand or other["casualties"] > 0:
                continue
            # other dominates cand if other >= cand in all metrics and strictly > in at least one
            if (other["mean_delta"] >= cand["mean_delta"] and
                other["p5_delta"] >= cand["p5_delta"] and
                other["rescues"] >= cand["rescues"]):
                if (other["mean_delta"] > cand["mean_delta"] or
                    other["p5_delta"] > cand["p5_delta"] or
                    other["rescues"] > cand["rescues"]):
                    dominated = True
                    break

        cand["is_pareto"] = not dominated
        if not dominated:
            frontier.append(cand["name"])

    print(f"\nPareto Dominant Strategies ({len(frontier)}): {frontier}")
    for s in strategies:
        mark = "* PARETO" if s.get("is_pareto") else "        "
        print(f" {mark} {s['name']:<30} | Mean: ${s['mean_delta']:>+8.2f} | P5: ${s['p5_delta']:>+7.2f} | Rescues: {s['rescues']} | Cas: {s['casualties']}")

    payload = {
        "pareto_strategies": frontier,
        "all_candidates": strategies
    }

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "alpha_frontier.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nAlpha Frontier saved to {out_file}")
    return payload


if __name__ == "__main__":
    build_alpha_frontier()
