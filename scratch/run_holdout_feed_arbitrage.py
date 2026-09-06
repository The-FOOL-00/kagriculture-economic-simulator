"""
Holdout Validation Suite for Top Causal Factor Combinations.
Executes >=100 paired matched seeds across closed-loop and open-loop meta opponents,
followed by >=100 completely unseen holdout seeds with zero parameter tuning.
"""

import os
import sys
import time
import json
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import scratch.causal_feed_arbitrage_agents as cfa
import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as lf
import opponents.replay_crop_dusta as cd
import opponents.replay_whyme_labs as whyme
import opponents.replay_kawatta_taido as kw

def wilson_ci(k, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))) / denom
    return max(0.0, center - half), min(1.0, center + half)

OPPONENTS = {
    "aethel_v2_closed": {
        "agent": v2.agent,
        "name": "Aethel_Refined_V2",
        "type": "CLOSED_LOOP"
    },
    "live_flooder_v1": {
        "agent": lf.agent,
        "name": "LiveFlooder_V1",
        "type": "CLOSED_LOOP"
    },
    "replay_crop_dusta": {
        "agent": cd.agent,
        "name": "Replay_Crop_Dusta",
        "type": "OPEN_LOOP"
    },
    "replay_whyme_labs": {
        "agent": whyme.agent,
        "name": "Replay_Whyme_Labs",
        "type": "OPEN_LOOP"
    },
}

def _run_single_match(item):
    cand_name, cand_agent, opp_key, seed, swapped = item
    o_agent = OPPONENTS[opp_key]["agent"]
    
    agent0 = o_agent if swapped else cand_agent
    agent1 = cand_agent if swapped else o_agent
    
    our_player = 1 if swapped else 0
    opp_player = 0 if swapped else 1
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    try:
        env.run([agent0, agent1])
        final_step = env.steps[-1]
        r_us = float(final_step[our_player]["reward"] or 0)
        r_opp = float(final_step[opp_player]["reward"] or 0)
        margin = r_us - r_opp
        won = 1 if r_us > r_opp else (0.5 if r_us == r_opp else 0)
        
        return {
            "cand_name": cand_name,
            "opp_key": opp_key,
            "seed": seed,
            "swapped": swapped,
            "reward_us": r_us,
            "reward_opp": r_opp,
            "margin": margin,
            "won": won
        }
    except Exception as e:
        return {
            "cand_name": cand_name,
            "opp_key": opp_key,
            "seed": seed,
            "swapped": swapped,
            "reward_us": 0.0,
            "reward_opp": 0.0,
            "margin": 0.0,
            "won": 0,
            "error": str(e)
        }

def run_holdout_validation(candidates_dict, num_seeds=100, is_holdout=False, max_workers=None):
    if max_workers is None:
        max_workers = min(16, os.cpu_count() or 4)
        
    seed_offset = 50000 if is_holdout else 10000
    seed_list = [seed_offset + i * 43 for i in range(num_seeds)]
    
    suite_name = "UNSEEN HOLDOUT SUITE" if is_holdout else "MATCHED EXTENDED VALIDATION SUITE"
    print(f"\n=======================================================")
    print(f"RUNNING {suite_name} ({num_seeds} seeds x 2 seats = {num_seeds*2} matches per opponent)")
    print(f"=======================================================")
    
    tasks = []
    for cand_name, cand_agent in candidates_dict.items():
        for opp_key in OPPONENTS:
            for seed in seed_list:
                for swapped in [False, True]:
                    tasks.append((cand_name, cand_agent, opp_key, seed, swapped))
                    
    total_matches = len(tasks)
    print(f"Total Matches to Run: {total_matches}")
    
    t0 = time.time()
    results = []
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed % 200 == 0 or completed == total_matches:
                elapsed = time.time() - t0
                print(f"Progress: {completed}/{total_matches} ({completed/total_matches*100:.1f}%) in {elapsed:.1f}s ({completed/max(0.1, elapsed):.1f} matches/sec)", flush=True)
                
    # Analyze by candidate
    print(f"\n{'='*100}")
    print(f"RESULTS: {suite_name}")
    print(f"{'='*100}")
    print(f"{'Candidate':<25} | {'Mean Score':>10} | {'Mean Margin':>11} | {'Win Rate (95% CI)':>22} | {'Worst Loss':>11}")
    print(f"{'-'*100}")
    
    by_cand = {}
    for r in results:
        cn = r["cand_name"]
        if cn not in by_cand:
            by_cand[cn] = []
        by_cand[cn].append(r)
        
    for cn, rows in by_cand.items():
        scores = [r["reward_us"] for r in rows]
        margins = [r["margin"] for r in rows]
        wins = sum(r["won"] for r in rows)
        n = len(rows)
        wr = wins / n
        ci_l, ci_u = wilson_ci(wins, n)
        worst_loss = min(margins)
        ci_str = f"{wr*100:5.1f}% [{ci_l*100:4.1f}%-{ci_u*100:4.1f}%]"
        print(f"{cn:<25} | ${np.mean(scores):9.1f} | ${np.mean(margins):+10.1f} | {ci_str:>22} | ${worst_loss:+10.1f}")
        
    print(f"{'='*100}\n")
    return results

if __name__ == "__main__":
    cands = {
        "Base V2 (Frozen)": cfa.agent_A,
        "C (Ext Wheat Only)": cfa.agent_C,
        "E (Dyn Liq + Ext Wheat)": cfa.agent_E,
        "H12 (All Three 12C)": cfa.agent_H,
    }
    # Extended matched validation (100 seeds)
    run_holdout_validation(cands, num_seeds=100, is_holdout=False)
    # Unseen holdout (100 seeds)
    run_holdout_validation(cands, num_seeds=100, is_holdout=True)
