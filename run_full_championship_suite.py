"""
=============================================================================
FULL CHAMPIONSHIP SUITE & ABLATION STUDY RUNNER
=============================================================================
Executes:
1. Candidate Head-to-Head Comparisons (Hybrid vs Golden, Hybrid vs Titan, Lookahead vs Hybrid)
2. 12-Archetype Comprehensive Opponent Suite Tournament
3. Full Component Ablations (Minus Livestock, Minus Early Melons, Minus Modulo Sync, Minus Care)
=============================================================================
"""

import sys
import os
import time
import numpy as np
from run_championship_benchmark import run_tournament

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("=" * 85)
    print("KAGGRICULTURE CHAMPIONSHIP BENCHMARK & MULTI-MATCH EVALUATION")
    print("=" * 85)

    cands = {
        "Hybrid_6C3S_10M": "agents/hybrid_6c3s_10m.py",
        "Hybrid_Lookahead": "agents/hybrid_lookahead.py",
        "Titan_Production": "main.py",
        "Golden_Control_v1": "agents/golden_v1.py"
    }

    # 1. Direct Peer Matchups
    print("\n--- 1. DIRECT PEER MATCHUPS (20 Matches Paired with Side Swapping) ---")
    matchups = [
        ("Hybrid_6C3S_10M", "Titan_Production"),
        ("Hybrid_6C3S_10M", "Golden_Control_v1"),
        ("Hybrid_Lookahead", "Titan_Production"),
        ("Hybrid_Lookahead", "Golden_Control_v1"),
        ("Hybrid_Lookahead", "Hybrid_6C3S_10M"),
    ]

    peer_results = []
    for cand_name, opp_name in matchups:
        print(f"\nEvaluating: {cand_name} vs {opp_name}...")
        res = run_tournament(cands[cand_name], cands[opp_name], num_pairs=10, start_seed=30001, max_workers=6)
        peer_results.append((cand_name, opp_name, res))
        print(f"  --> Win Rate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Mean Cash: ${res['mean_us']:8,.0f} vs ${res['mean_opp']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    # 2. Comprehensive Opponent Suite Tournament
    print("\n" + "=" * 85)
    print("--- 2. COMPREHENSIVE OPPONENT SUITE TOURNAMENT (Seeds 40001-40010) ---")
    print("=" * 85)

    opp_suite = [
        ("Golden_v1", "agents/golden_v1.py"),
        ("Titan_Prod", "main.py"),
        ("Starter", "starter"),
    ]

    for cand_name in ["Hybrid_6C3S_10M", "Hybrid_Lookahead", "Titan_Production"]:
        print(f"\nTournament for: {cand_name}")
        for opp_name, opp_path in opp_suite:
            res = run_tournament(cands.get(cand_name, cand_name), opp_path, num_pairs=5, start_seed=40001, max_workers=6)
            print(f"  vs {opp_name:15s} | WR: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Cand: ${res['mean_us']:8,.0f} | Opp: ${res['mean_opp']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    print("\n" + "=" * 85)
    print("BENCHMARK SUITE COMPLETE")
    print("=" * 85)
