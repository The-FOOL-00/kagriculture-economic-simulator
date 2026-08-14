"""
=============================================================================
MULTI-ARCHETYPE TOURNAMENT SUITE
=============================================================================
Runs multi-seed tournament of candidate agent against all strategic archetypes.
=============================================================================
"""

import os
import sys
import numpy as np
from benchmark_harness import run_benchmark


def run_full_tournament(candidate_path="main.py", matches_per_archetype=10):
    print("=" * 75)
    print(f"RUNNING MULTI-ARCHETYPE TOURNAMENT FOR: {candidate_path}")
    print("=" * 75)

    archetypes = [
        ("Starter", "starter"),
        ("Golden Control v1", "agents/golden_v1.py"),
    ]

    scoreboard = []

    for name, opp_path in archetypes:
        print(f"\n>>> Running Matchup: Candidate vs {name} ({matches_per_archetype} Matches) <<<")
        res = run_benchmark(
            agent0=candidate_path,
            agent1=opp_path,
            num_matches=matches_per_archetype,
            start_seed=12000,
            swap_sides=True
        )
        scoreboard.append({
            "archetype": name,
            "wins": res["wins"],
            "losses": res["losses"],
            "ties": res["ties"],
            "win_rate": res["win_rate"],
            "mean_cand": res["mean_r0"],
            "mean_opp": res["mean_r1"],
            "margin": res["mean_diff"]
        })

    print("\n" + "=" * 75)
    print(f"MULTI-ARCHETYPE TOURNAMENT FINAL SCOREBOARD")
    print("=" * 75)
    print(f"{'Opponent Archetype':25s} | {'Wins':6s} | {'Losses':6s} | {'Win Rate':9s} | {'Cand Cash':12s} | {'Opp Cash':12s} | {'Advantage'}")
    print("-" * 90)
    for row in scoreboard:
        print(f"{row['archetype']:25s} | {row['wins']:6d} | {row['losses']:6d} | {row['win_rate']:8.1f}% | ${row['mean_cand']:10,.2f} | ${row['mean_opp']:10,.2f} | ${row['margin']:+10,.2f}")

    print("=" * 75)


if __name__ == "__main__":
    cand = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    run_full_tournament(cand, cnt)
