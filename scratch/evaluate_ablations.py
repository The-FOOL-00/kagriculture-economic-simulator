import os
import sys
import json
import time
import pandas as pd
import numpy as np

# Ensure project root in sys.path
sys.path.insert(0, r"c:\Users\Sundareswaran\Kagriculture")
from tournament_engine import run_paired_tournament

candidates = {
    "A (V2 Base)": "candidates/counterstrategy_ablation/candidate_A.py",
    "B (Cap12)": "candidates/counterstrategy_ablation/candidate_B.py",
    "C (EarlyRamp)": "candidates/counterstrategy_ablation/candidate_C.py",
    "D (Preempt)": "candidates/counterstrategy_ablation/candidate_D.py",
    "E (Cap12+Ramp)": "candidates/counterstrategy_ablation/candidate_E.py",
    "F (Cap12+Preempt)": "candidates/counterstrategy_ablation/candidate_F.py",
    "G (Ramp+Preempt)": "candidates/counterstrategy_ablation/candidate_G.py",
    "H (All3)": "candidates/counterstrategy_ablation/candidate_H.py",
}

opponents = {
    "LiveFlooder": "opponents/live_flooder_v1.py",
    "ReplayKawatta": "opponents/replay_kawatta_taido.py",
    "ReplayMtN": "opponents/replay_mtn.py",
    "AethelV1": "main.py",
}

def main():
    # 10 matched seeds (20 games per matchup x 4 opponents = 80 games per candidate)
    seeds = [42, 100, 2026, 777, 999, 1234, 5555, 8888, 10101, 20202]

    print("=" * 90)
    print(f"EVALUATING ABLATION CANDIDATES A THROUGH H ({len(seeds)} Seeds, Paired & Swapped = {len(seeds)*2} games/matchup)")
    print("=" * 90)

    all_results = []
    matrix_margin = {}
    matrix_wr = {}

    t0_total = time.time()

    for cand_name, cand_path in candidates.items():
        matrix_margin[cand_name] = {}
        matrix_wr[cand_name] = {}
        print(f"\n---> Evaluating Candidate: {cand_name}")
        sys.stdout.flush()
        t0_cand = time.time()
        
        for opp_name, opp_path in opponents.items():
            t0_match = time.time()
            res = run_paired_tournament(cand_path, opp_path, seeds=seeds, num_pairs=len(seeds), max_workers=6)
            elapsed = time.time() - t0_match
            
            matrix_margin[cand_name][opp_name] = res['margin']
            matrix_wr[cand_name][opp_name] = res['win_rate']
            
            print(f"  vs {opp_name:15s}: WR = {res['win_rate']:5.1f}% | Margin = ${res['margin']:+8.0f} | Cand = ${res['mean_us']:7.0f} | Opp = ${res['mean_opp']:7.0f} ({elapsed:.1f}s)")
            sys.stdout.flush()
            
            all_results.append({
                'candidate': cand_name,
                'opponent': opp_name,
                'win_rate': res['win_rate'],
                'margin': res['margin'],
                'std_margin': res['std_margin'],
                'cand_mean': res['mean_us'],
                'opp_mean': res['mean_opp'],
                'worst_drawdown': res['worst_drawdown'],
                'games': res['games']
            })
            
        print(f"Candidate {cand_name} completed in {time.time() - t0_cand:.1f}s")
        sys.stdout.flush()

    # Save summary
    df = pd.DataFrame(all_results)
    df.to_csv("scratch/ablation_evaluation_results.csv", index=False)

    print("\n" + "=" * 90)
    print("OVERALL CANDIDATE RANKINGS (Aggregated Across All 4 Opponents)")
    print("=" * 90)
    agg = df.groupby('candidate').agg({
        'win_rate': 'mean',
        'margin': 'mean',
        'cand_mean': 'mean',
        'opp_mean': 'mean',
        'worst_drawdown': 'min'
    }).reset_index().sort_values(by='margin', ascending=False)
    print(agg.to_string(index=False))

    print("\n" + "=" * 90)
    print("MEAN MARGIN MATRIX ($)")
    print("=" * 90)
    df_margin = pd.DataFrame(matrix_margin).T
    print(df_margin.round(0).to_string())

    print("\n" + "=" * 90)
    print("WIN RATE MATRIX (%)")
    print("=" * 90)
    df_wr = pd.DataFrame(matrix_wr).T
    print(df_wr.round(1).to_string())

    print(f"\nFull ablation evaluation finished in {time.time() - t0_total:.1f}s.")

if __name__ == "__main__":
    main()
