"""
Perturbation Robustness & Direct Frozen V2 Head-to-Head Tournament
1. Perturbation Suite (50 Seeds per scenario):
   - Baseline ($3,000)
   - Low Starting Money ($2,000)
   - High Starting Money ($4,000)
   - Price Inversion (Strawberry $80, Wool $250)
   - Feed Price Spike (Wheat $50)
2. Direct Frozen V2 Head-to-Head Tournament (100 Seeds 5000-5099, Alternating Seats):
   - 50 games Candidate P0, 50 games Candidate P1
   - Complete cash ledger, margins, win rate, and phase breakdown.
"""

import sys
import os
import time
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_temporal_v2 import agent as candidate_v2_agent
from candidates.candidate_cl_economic_v1 import agent as baseline_agent

CHECKPOINT_DAYS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

def _run_h2h_match(item):
    cand_agent_mod, seed, cand_seat = item
    
    mod = __import__(cand_agent_mod, fromlist=["agent"])
    cand_agent = mod.agent
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    if cand_seat == 0:
        agents = [cand_agent, v2_agent]
        p_cand, p_v2 = 0, 1
    else:
        agents = [v2_agent, cand_agent]
        p_cand, p_v2 = 1, 0
        
    try:
        env.run(agents)
        steps = env.steps
        
        cand_reward = float(steps[-1][p_cand].get("reward") or 0.0)
        v2_reward = float(steps[-1][p_v2].get("reward") or 0.0)
        
        # Day cash curves
        cand_cash_curve = {}
        v2_cash_curve = {}
        for d in CHECKPOINT_DAYS:
            step_idx = min(d * 24, len(steps) - 1)
            c_f = steps[step_idx][p_cand]["observation"]["farms"][p_cand]
            v_f = steps[step_idx][p_v2]["observation"]["farms"][p_v2]
            cand_cash_curve[d] = float(c_f["money"])
            v2_cash_curve[d] = float(v_f["money"])
            
        margin = cand_reward - v2_reward
        win = 1 if cand_reward > v2_reward else (0 if v2_reward > cand_reward else 0.5)
        
        return {
            "seed": seed,
            "cand_seat": cand_seat,
            "cand_reward": cand_reward,
            "v2_reward": v2_reward,
            "margin": margin,
            "win": win,
            "cand_cash_curve": cand_cash_curve,
            "v2_cash_curve": v2_cash_curve,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed,
            "cand_seat": cand_seat,
            "cand_reward": 0.0,
            "v2_reward": 0.0,
            "margin": 0.0,
            "win": 0,
            "cand_cash_curve": {},
            "v2_cash_curve": {},
            "error": str(e)
        }

def run_h2h_tournament(cand_mod="candidates.candidate_cl_temporal_v2", num_matches=100, start_seed=5000, max_workers=10):
    print("=" * 95)
    print(f"DIRECT HEAD-TO-HEAD TOURNAMENT: {cand_mod} vs FROZEN V2")
    print(f"Matches: {num_matches} (Seeds {start_seed}-{start_seed + num_matches - 1}) | Alternating Seats")
    print("=" * 95)
    
    tasks = []
    for i in range(num_matches):
        seed = start_seed + i
        cand_seat = 0 if i % 2 == 0 else 1
        tasks.append((cand_mod, seed, cand_seat))
        
    results = []
    t0 = time.time()
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_h2h_match, t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % 20 == 0 or completed == num_matches:
                print(f"H2H Progress: {completed}/{num_matches} ({completed/num_matches*100:.1f}%) in {time.time()-t0:.1f}s")
                
    valid = [r for r in results if r["error"] is None]
    cand_rewards = [r["cand_reward"] for r in valid]
    v2_rewards = [r["v2_reward"] for r in valid]
    margins = [r["margin"] for r in valid]
    wins = sum(1 for r in valid if r["win"] == 1)
    losses = sum(1 for r in valid if r["win"] == 0)
    ties = sum(1 for r in valid if r["win"] == 0.5)
    
    mean_cand = float(np.mean(cand_rewards))
    std_cand = float(np.std(cand_rewards))
    mean_v2 = float(np.mean(v2_rewards))
    std_v2 = float(np.std(v2_rewards))
    mean_margin = float(np.mean(margins))
    std_margin = float(np.std(margins))
    med_margin = float(np.median(margins))
    ci95 = 1.96 * (std_margin / np.sqrt(len(margins)))
    
    # Average cumulative cash curves
    avg_cand_cash = {d: float(np.mean([r["cand_cash_curve"][d] for r in valid])) for d in CHECKPOINT_DAYS}
    avg_v2_cash = {d: float(np.mean([r["v2_cash_curve"][d] for r in valid])) for d in CHECKPOINT_DAYS}
    
    print("\n" + "=" * 90)
    print("HEAD-TO-HEAD TOURNAMENT RESULTS SUMMARY")
    print("=" * 90)
    print(f"Total Matches:    {len(valid)} ({num_matches - len(valid)} errors)")
    print(f"Record (W-L-T):   {wins} Wins - {losses} Losses - {ties} Ties ({wins/len(valid)*100:.1f}% Win Rate)")
    print(f"Candidate Cash:   ${mean_cand:10,.2f} +/- ${std_cand:8,.2f}")
    print(f"Frozen V2 Cash:   ${mean_v2:10,.2f} +/- ${std_v2:8,.2f}")
    print(f"Net Mean Margin:  ${mean_margin:+10,.2f} +/- ${ci95:8,.2f} (95% CI)")
    print(f"Net Median Margin:${med_margin:+10,.2f}")
    print("-" * 90)
    print(f"{'Day':<6} | {'Candidate Cash ($)':<20} | {'Frozen V2 Cash ($)':<20} | {'Cash Margin (Cand - V2)':<24}")
    print("-" * 90)
    for d in CHECKPOINT_DAYS:
        cc = avg_cand_cash[d]
        vc = avg_v2_cash[d]
        print(f"Day {d:<2} | ${cc:18,.1f} | ${vc:18,.1f} | ${cc - vc:+22,.1f}")
    print("=" * 90)
    
    summary = {
        "candidate": cand_mod,
        "matches": len(valid),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / len(valid),
        "mean_cand_reward": mean_cand,
        "std_cand_reward": std_cand,
        "mean_v2_reward": mean_v2,
        "std_v2_reward": std_v2,
        "mean_margin": mean_margin,
        "median_margin": med_margin,
        "ci95": ci95,
        "cand_cash_curve": avg_cand_cash,
        "v2_cash_curve": avg_v2_cash
    }
    
    with open("scratch/h2h_v2_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved H2H results to scratch/h2h_v2_results.json")
    return summary

if __name__ == "__main__":
    run_h2h_tournament()
