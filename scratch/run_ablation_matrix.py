import os
import sys
import time
import json
import math
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root in path
project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def _run_single_match(item):
    cand_path, opp_path, seed, swapped, cand_name, opp_name = item
    agent0 = opp_path if swapped else cand_path
    agent1 = cand_path if swapped else opp_path
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([agent0, agent1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        r0 = float(final_step[0].reward or 0.0)
        r1 = float(final_step[1].reward or 0.0)
        
        r_cand = r1 if swapped else r0
        r_opp = r0 if swapped else r1
        margin = r_cand - r_opp
        win = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
        
        return {
            'cand': cand_name,
            'opp': opp_name,
            'seed': seed,
            'swapped': swapped,
            'r_cand': r_cand,
            'r_opp': r_opp,
            'margin': margin,
            'win': win,
            'elapsed': elapsed
        }
    except Exception as e:
        return {
            'cand': cand_name,
            'opp': opp_name,
            'seed': seed,
            'swapped': swapped,
            'r_cand': 0.0,
            'r_opp': 0.0,
            'margin': 0.0,
            'win': 0.0,
            'error': str(e)
        }

def run_discovery_suite(candidates, opponents, seeds, max_workers=6):
    print("=" * 85)
    print(f"RAPID DISCOVERY PHASE: {len(candidates)} Candidates x {len(opponents)} Opponents x {len(seeds)} Seeds (Symmetric)")
    print(f"Total Matches to Run: {len(candidates) * len(opponents) * len(seeds) * 2}")
    print("=" * 85)
    
    tasks = []
    for cand_name, cand_path in candidates.items():
        for opp_name, opp_path in opponents.items():
            for s in seeds:
                # Normal: cand as P0
                tasks.append((cand_path, opp_path, s, False, cand_name, opp_name))
                # Swapped: cand as P1
                tasks.append((cand_path, opp_path, s, True, cand_name, opp_name))
                
    results = []
    t_start = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, t): t for t in tasks}
        completed = 0
        total = len(tasks)
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 20 == 0 or completed == total:
                print(f"Completed {completed}/{total} matches ({(completed/total)*100:.1f}%) in {time.time() - t_start:.1f}s")
                
    df = pd.DataFrame(results)
    
    # Summarize by candidate
    print("\n" + "=" * 85)
    print("DISCOVERY PHASE SUMMARY ACROSS ALL OPPONENTS")
    print("=" * 85)
    
    cand_summary = []
    for c_name, c_df in df.groupby('cand'):
        wr = c_df['win'].mean() * 100
        mean_r = c_df['r_cand'].mean()
        mean_opp_r = c_df['r_opp'].mean()
        mean_margin = c_df['margin'].mean()
        worst_loss = c_df['margin'].min()
        std_margin = c_df['margin'].std()
        
        cand_summary.append({
            'Candidate': c_name,
            'Games': len(c_df),
            'WinRate': wr,
            'MeanReward': mean_r,
            'MeanOppReward': mean_opp_r,
            'MeanMargin': mean_margin,
            'WorstLoss': worst_loss,
            'StdMargin': std_margin
        })
        
    sum_df = pd.DataFrame(cand_summary).sort_values(by='MeanMargin', ascending=False).reset_index(drop=True)
    print(sum_df.to_string(index=False))
    
    # Detailed breakdown by opponent
    print("\n" + "=" * 85)
    print("PER-OPPONENT MEAN MARGIN BREAKDOWN")
    print("=" * 85)
    pivot_margin = df.pivot_table(index='cand', columns='opp', values='margin', aggfunc='mean')
    print(pivot_margin.round(1).to_string())
    
    print("\n" + "=" * 85)
    print("PER-OPPONENT WIN RATE (%) BREAKDOWN")
    print("=" * 85)
    pivot_wr = df.pivot_table(index='cand', columns='opp', values='win', aggfunc=lambda x: x.mean() * 100)
    print(pivot_wr.round(1).to_string())
    
    # Save results to json
    with open("scratch/rapid_discovery_results.json", "w", encoding="utf-8") as f:
        json.dump({
            'summary': cand_summary,
            'raw_results': results
        }, f, indent=2)
        
    return df, sum_df

if __name__ == "__main__":
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
        "AethelV1": "main.py"
    }
    
    # 20 matched seeds for discovery
    discovery_seeds = [42, 100, 2026, 777, 999, 1234, 5555, 8888, 10101, 20202,
                       30303, 40404, 50505, 60606, 70707, 80808, 90909, 12121, 23232, 34343]
                       
    run_discovery_suite(candidates, opponents, discovery_seeds, max_workers=6)
