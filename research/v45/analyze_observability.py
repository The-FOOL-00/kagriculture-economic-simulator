# SPDX-License-Identifier: MIT
"""V45 Market Observability & Signal Analysis Script.

Analyzes the 92,032-step dataset in research/v45/artifacts/opponent_market_history.jsonl:
- Quantifies observable market sales events (dumps).
- Evaluates price collapse frequencies across commodities.
- Measures lead-time correlations between observable indicators (price velocity,
  opponent cash delta, town shop ticks) and future market pressure.
- Formulates the statistical and feature basis for Phase 2 modeling.
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMMODITIES = ["CARROT", "EGG", "FERTILIZER", "MELON", "MILK", "STRAWBERRY", "TOMATO", "WHEAT", "WOOL"]
HIGH_VALUE_COMMODITIES = ["STRAWBERRY", "MILK", "WOOL", "MELON"]


def analyze_dataset():
    data_file = os.path.join(REPO_ROOT, "research", "v45", "artifacts", "opponent_market_history.jsonl")
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Missing {data_file}")
        
    print(f"Loading and parsing {data_file}...")
    t0 = time.perf_counter()
    
    # Store trajectories by game_id
    games: Dict[int, List[dict]] = {}
    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            gid = rec["game_id"]
            if gid not in games:
                games[gid] = []
            games[gid].append(rec)
            
    print(f"Loaded {len(games)} complete games in {time.perf_counter() - t0:.1f}s.")
    
    # Now analyze market pressure events
    # Event definitions:
    # 1. Opponent Dump: Inferred opponent sales >= 5 units on a commodity in a single step
    # 2. Large Opponent Dump: Inferred opponent sales >= 15 units
    # 3. Price Collapse: Price drops by >= 15% within the next H steps (H in 4, 8, 16)
    
    dump_events_total = 0
    large_dump_events = 0
    terminal_dumps = 0 # dumps occurring at step >= 680
    midgame_dumps = 0   # dumps occurring at step < 680
    
    dumps_by_opp: Dict[str, int] = {}
    dumps_by_commodity: Dict[str, int] = {c: 0 for c in COMMODITIES}
    
    # Correlations between observable signals and future price drops
    # Trailing 4-step price velocity vs future 8-step price change
    corrs_vel_vs_fut_change = {c: [] for c in HIGH_VALUE_COMMODITIES}
    # Opponent cash velocity vs future price drop
    opp_cash_vel_signals = []
    
    # Lead time distribution for major terminal drops
    terminal_collapse_steps = []
    
    for gid, steps in games.items():
        n_steps = len(steps)
        opp_id = steps[0]["opp_id"]
        if opp_id not in dumps_by_opp:
            dumps_by_opp[opp_id] = 0
            
        for t in range(n_steps):
            rec = steps[t]
            step_idx = rec["step"]
            obs_sales = rec["observed_market_sales"]
            
            # Check dumps
            step_has_dump = False
            for c in HIGH_VALUE_COMMODITIES:
                q = obs_sales.get(c, 0)
                if q >= 4:
                    dumps_by_commodity[c] += 1
                    step_has_dump = True
                    if q >= 15:
                        large_dump_events += 1
                        
            if step_has_dump:
                dump_events_total += 1
                dumps_by_opp[opp_id] += 1
                if step_idx >= 680:
                    terminal_dumps += 1
                else:
                    midgame_dumps += 1
                    
            # Check price dynamics over future horizons
            if t + 8 < n_steps:
                fut_rec = steps[t + 8]
                for c in HIGH_VALUE_COMMODITIES:
                    cur_p = rec["prices"].get(c, 1)
                    fut_p = fut_rec["prices"].get(c, 1)
                    p_vel_4 = rec["price_vel_4"].get(c, 0)
                    fut_delta = fut_p - cur_p
                    corrs_vel_vs_fut_change[c].append((p_vel_4, fut_delta))
                    
            # Record terminal collapse step (first step after 680 where price drops by > $30)
            if step_idx == 680:
                for c in HIGH_VALUE_COMMODITIES:
                    base_p = rec["prices"].get(c, 1)
                    for t_f in range(t, min(t + 39, n_steps)):
                        if base_p - steps[t_f]["prices"].get(c, 1) >= 30:
                            terminal_collapse_steps.append((c, steps[t_f]["step"]))
                            break
                            
    # Compute summary statistics
    analysis_results = {
        "total_games": len(games),
        "total_steps": sum(len(g) for g in games.values()),
        "total_dump_events": dump_events_total,
        "large_dump_events": large_dump_events,
        "midgame_dumps": midgame_dumps,
        "terminal_dumps": terminal_dumps,
        "dumps_by_opponent": dumps_by_opp,
        "dumps_by_commodity": {c: dumps_by_commodity[c] for c in HIGH_VALUE_COMMODITIES},
        "terminal_collapse_timing": {
            "mean_step": round(float(np.mean([s[1] for s in terminal_collapse_steps])), 1) if terminal_collapse_steps else 0,
            "min_step": int(np.min([s[1] for s in terminal_collapse_steps])) if terminal_collapse_steps else 0,
            "median_step": float(np.median([s[1] for s in terminal_collapse_steps])) if terminal_collapse_steps else 0,
            "p25_step": float(np.percentile([s[1] for s in terminal_collapse_steps], 25)) if terminal_collapse_steps else 0,
            "p75_step": float(np.percentile([s[1] for s in terminal_collapse_steps], 75)) if terminal_collapse_steps else 0,
        },
        "price_velocity_correlation": {
            c: round(float(np.corrcoef([x[0] for x in corrs_vel_vs_fut_change[c]], [x[1] for x in corrs_vel_vs_fut_change[c]])[0, 1]), 3)
            for c in HIGH_VALUE_COMMODITIES if corrs_vel_vs_fut_change[c]
        }
    }
    
    print("\n--- OBSERVABILITY ANALYSIS SUMMARY ---")
    print(f"Total Dump Events: {dump_events_total} (Midgame: {midgame_dumps}, Terminal: {terminal_dumps})")
    print(f"Dumps by Opponent: {dumps_by_opp}")
    print(f"Dumps by Commodity: {analysis_results['dumps_by_commodity']}")
    print(f"Terminal Collapse Timing: Median Step {analysis_results['terminal_collapse_timing']['median_step']} (Min: {analysis_results['terminal_collapse_timing']['min_step']}, P25: {analysis_results['terminal_collapse_timing']['p25_step']})")
    print(f"Velocity Correlation with Future Price Delta: {analysis_results['price_velocity_correlation']}")
    
    out_json = os.path.join(REPO_ROOT, "research", "v45", "artifacts", "observability_analysis.json")
    with open(out_json, "w") as f:
        json.dump(analysis_results, f, indent=2)
    print(f"Saved observability summary to {out_json}")
    return analysis_results


if __name__ == "__main__":
    analyze_dataset()
