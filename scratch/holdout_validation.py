import os
import sys
import time
import pandas as pd
import numpy as np

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tournament_engine import run_paired_tournament

def main():
    print("=" * 80)
    print("HOLDOUT VALIDATION: CANDIDATE B (CAP12) VS CANDIDATE A (V2 BASE) & REPLAY ECOSYSTEM")
    print("=" * 80)

    # 1. Direct Head-to-Head: Candidate B vs Candidate A (50 seeds = 100 paired games)
    cand_b = "candidates/counterstrategy_ablation/candidate_B.py"
    cand_a = "candidates/counterstrategy_ablation/candidate_A.py"
    
    seeds_h2h = [30000 + i * 17 for i in range(50)]
    print(f"\n---> Running Direct H2H: Candidate B (Cap12) vs Candidate A (V2 Base) [50 seeds = 100 games]...")
    t0 = time.time()
    res_h2h = run_paired_tournament(cand_b, cand_a, seeds=seeds_h2h, max_workers=6)
    elapsed_h2h = time.time() - t0
    print(f"H2H Done in {elapsed_h2h:.1f}s:")
    print(f"  Candidate B Win Rate: {res_h2h['win_rate']:.1f}% [{res_h2h['ci_95'][0]:.1f}% - {res_h2h['ci_95'][1]:.1f}%]")
    print(f"  Candidate B Mean Margin: ${res_h2h['margin']:+,.1f}")
    print(f"  Candidate B Mean Cash: ${res_h2h['mean_us']:,.1f} | Candidate A Mean Cash: ${res_h2h['mean_opp']:,.1f}")
    print(f"  Worst Drawdown: ${res_h2h['worst_drawdown']:+,.1f}")

    # 2. Ecosystem Evaluation of Candidate B vs Replays & Standard Opponents
    opponents = {
        "Replay_MtN (#1)": "opponents/replay_mtn.py",
        "Replay_CropDusta (#2)": "opponents/replay_crop_dusta.py",
        "Replay_Yuan800 (#3)": "opponents/replay_yuan800.py",
        "Replay_WhyMeLabs (#5)": "opponents/replay_whyme_labs.py",
        "Replay_Kawatta (Flooder)": "opponents/replay_kawatta_taido.py",
        "LiveFlooder_V1 (Synthetic)": "opponents/live_flooder_v1.py",
        "Aethel_Prime_V1": "candidates/slot1_aethel_prime_v1.py"
    }

    seeds_eco = [50000 + i * 31 for i in range(25)] # 25 seeds = 50 games per matchup
    
    print("\n" + "=" * 80)
    print("CANDIDATE B (CAP12) VS COMPREHENSIVE REPLAY & ADVERSARY ECOSYSTEM (25 Seeds = 50 Games each)")
    print("=" * 80)
    
    records = []
    for opp_name, opp_path in opponents.items():
        print(f"\n---> Evaluating vs {opp_name}...")
        t_start = time.time()
        res = run_paired_tournament(cand_b, opp_path, seeds=seeds_eco, max_workers=6)
        dur = time.time() - t_start
        print(f"  WR: {res['win_rate']:.1f}% [{res['ci_95'][0]:.1f}% - {res['ci_95'][1]:.1f}%] | Margin: ${res['margin']:+,.1f} | Cand: ${res['mean_us']:,.1f} | Opp: ${res['mean_opp']:,.1f} ({dur:.1f}s)")
        records.append({
            "opponent": opp_name,
            "win_rate": res["win_rate"],
            "ci_lower": res["ci_95"][0],
            "ci_upper": res["ci_95"][1],
            "mean_margin": res["margin"],
            "cand_mean": res["mean_us"],
            "opp_mean": res["mean_opp"],
            "worst_drawdown": res["worst_drawdown"]
        })

    df = pd.DataFrame(records)
    print("\n" + "=" * 80)
    print("FINAL CANDIDATE B VALIDATION SUMMARY TABLE")
    print("=" * 80)
    print(df.to_string(index=False))

    # Also run Candidate A (Base V2) against the same replays for a direct comparison!
    print("\n" + "=" * 80)
    print("CANDIDATE A (BASE V2) BENCHMARK COMPARISON ACROSS SAME REPLAYS")
    print("=" * 80)
    records_a = []
    for opp_name, opp_path in opponents.items():
        print(f"\n---> Evaluating Candidate A vs {opp_name}...")
        t_start = time.time()
        res = run_paired_tournament(cand_a, opp_path, seeds=seeds_eco, max_workers=6)
        dur = time.time() - t_start
        print(f"  WR: {res['win_rate']:.1f}% [{res['ci_95'][0]:.1f}% - {res['ci_95'][1]:.1f}%] | Margin: ${res['margin']:+,.1f} | Cand: ${res['mean_us']:,.1f} | Opp: ${res['mean_opp']:,.1f} ({dur:.1f}s)")
        records_a.append({
            "opponent": opp_name,
            "win_rate": res["win_rate"],
            "ci_lower": res["ci_95"][0],
            "ci_upper": res["ci_95"][1],
            "mean_margin": res["margin"],
            "cand_mean": res["mean_us"],
            "opp_mean": res["mean_opp"],
            "worst_drawdown": res["worst_drawdown"]
        })
    df_a = pd.DataFrame(records_a)
    print("\n" + "=" * 80)
    print("FINAL CANDIDATE A (BASE V2) VALIDATION SUMMARY TABLE")
    print("=" * 80)
    print(df_a.to_string(index=False))

if __name__ == "__main__":
    main()
