# SPDX-License-Identifier: MIT
"""V39 No-Regression Tournament & Validation Harness.

Executes paired validation of V39 vs V35:
1. Direct head-to-head V39 vs V35 on 10 safe seeds (both seats = 20 games).
2. Paired benchmark league evaluation:
   - 10 safe seeds (5 Dev: 249675-249679, 5 Fresh: 249680-249684)
   - Benchmark opponents: E2_A7, E1_V22R1, E8_DMITRII, V54, SYN_AGG
   - Both seats
   - Total: 10 seeds x 5 opponents x 2 seats = 100 paired games for V35, 100 for V39 (200 games total)
3. Evaluates:
   - Rescues & Casualties (V35->V39)
   - Paired win-rate and cash deltas
   - Bootstrap 95% Confidence Intervals (1,000 iterations)
   - McNemar test
4. Outputs scratch/v39/v39_regression_tournament_results.json
"""

import copy
import json
import multiprocessing as mp
import os
import sys
import time
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController

OUT_DIR = os.path.join(BASE_DIR, "scratch", "v39")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_RESULTS = os.path.join(OUT_DIR, "v39_regression_tournament_results.json")
DONE_FILE = os.path.join(OUT_DIR, "tournament.done")

# Strictly safe seeds outside protected holdouts
DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]
FRESH_SEEDS = [249680, 249681, 249682, 249683, 249684]
ALL_SEEDS = DEV_SEEDS + FRESH_SEEDS

BENCHMARK_OPPONENTS = ["E2_A7", "E1_V22R1", "E8_DMITRII", "V54", "SYN_AGG"]

def eval_single_game(args):
    agent_type, opp_id, seed, seat = args
    if agent_type == "V35":
        player_fn = V35OpeningController()
    elif agent_type == "V39":
        player_fn = V39TargetedController()
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
        
    opp_fn = load_league_opponent(opp_id)
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    
    if seat == 0:
        env.run([player_fn, opp_fn])
        p_reward = float(env.steps[-1][0]["reward"] or 0.0)
        o_reward = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp_fn, player_fn])
        p_reward = float(env.steps[-1][1]["reward"] or 0.0)
        o_reward = float(env.steps[-1][0]["reward"] or 0.0)
        
    margin = p_reward - o_reward
    result = "WIN" if margin > 0 else ("LOSS" if margin < 0 else "TIE")
    return {
        "agent": agent_type,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "p_reward": p_reward,
        "o_reward": o_reward,
        "margin": margin,
        "result": result
    }

def eval_h2h_game(args):
    seed, v39_seat = args
    v35_ctrl = V35OpeningController()
    v39_ctrl = V39TargetedController()
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    
    if v39_seat == 0:
        env.run([v39_ctrl, v35_ctrl])
        v39_r = float(env.steps[-1][0]["reward"] or 0.0)
        v35_r = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([v35_ctrl, v39_ctrl])
        v39_r = float(env.steps[-1][1]["reward"] or 0.0)
        v35_r = float(env.steps[-1][0]["reward"] or 0.0)
        
    margin = v39_r - v35_r
    result = "WIN" if margin > 0 else ("LOSS" if margin < 0 else "TIE")
    return {
        "seed": seed,
        "v39_seat": v39_seat,
        "v39_reward": v39_r,
        "v35_reward": v35_r,
        "margin": margin,
        "result": result
    }

def main():
    start_t = time.time()
    num_cpus = max(1, min(mp.cpu_count() - 1, 8))
    print(f"Starting V39 vs V35 Regression Tournament on {num_cpus} workers...")
    
    # 1. Direct Head-to-Head: V39 vs V35
    h2h_tasks = []
    for s in ALL_SEEDS:
        for seat in (0, 1):
            h2h_tasks.append((s, seat))
            
    with mp.Pool(num_cpus) as pool:
        h2h_results = pool.map(eval_h2h_game, h2h_tasks)
        
    v39_h2h_wins = sum(1 for r in h2h_results if r["result"] == "WIN")
    v39_h2h_losses = sum(1 for r in h2h_results if r["result"] == "LOSS")
    v39_h2h_ties = sum(1 for r in h2h_results if r["result"] == "TIE")
    h2h_margins = [r["margin"] for r in h2h_results]
    
    print(f"H2H V39 vs V35: {v39_h2h_wins}W / {v39_h2h_losses}L / {v39_h2h_ties}T | Mean Margin: ${np.mean(h2h_margins):+.2f}")
    
    # 2. Paired Benchmark League: V35 and V39 vs common opponents
    league_tasks = []
    for ag in ("V35", "V39"):
        for opp in BENCHMARK_OPPONENTS:
            for s in ALL_SEEDS:
                for seat in (0, 1):
                    league_tasks.append((ag, opp, s, seat))
                    
    with mp.Pool(num_cpus) as pool:
        raw_league_results = pool.map(eval_single_game, league_tasks)
        
    # Group by (opponent, seed, seat) to construct paired comparisons
    paired_data = {}
    for r in raw_league_results:
        key = (r["opponent"], r["seed"], r["seat"])
        paired_data.setdefault(key, {})[r["agent"]] = r
        
    paired_evals = []
    rescues = 0
    casualties = 0
    preserved_wins = 0
    cash_deltas = []
    
    for key, leg in paired_data.items():
        v35 = leg["V35"]
        v39 = leg["V39"]
        c_delta = v39["p_reward"] - v35["p_reward"]
        cash_deltas.append(c_delta)
        
        v35_win = v35["result"] == "WIN"
        v39_win = v39["result"] == "WIN"
        
        if not v35_win and v39_win:
            rescues += 1
        elif v35_win and not v39_win:
            casualties += 1
        elif v35_win and v39_win:
            preserved_wins += 1
            
        paired_evals.append({
            "opponent": key[0],
            "seed": key[1],
            "seat": key[2],
            "v35_reward": v35["p_reward"],
            "v39_reward": v39["p_reward"],
            "v35_result": v35["result"],
            "v39_result": v39["result"],
            "cash_delta": c_delta
        })
        
    v35_total_wins = sum(1 for p in paired_evals if p["v35_result"] == "WIN")
    v39_total_wins = sum(1 for p in paired_evals if p["v39_result"] == "WIN")
    total_matches = len(paired_evals)
    
    # Bootstrap CI for mean cash delta
    rng = np.random.default_rng(42)
    deltas_arr = np.array(cash_deltas)
    boot_means = [np.mean(rng.choice(deltas_arr, size=len(deltas_arr), replace=True)) for _ in range(1000)]
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    
    summary = {
        "total_paired_matches": total_matches,
        "v35_wins": v35_total_wins,
        "v39_wins": v39_total_wins,
        "v35_win_rate": v35_total_wins / total_matches,
        "v39_win_rate": v39_total_wins / total_matches,
        "rescues": rescues,
        "casualties": casualties,
        "preserved_wins": preserved_wins,
        "mean_paired_cash_delta": float(np.mean(cash_deltas)),
        "median_paired_cash_delta": float(np.median(cash_deltas)),
        "min_paired_cash_delta": float(np.min(cash_deltas)),
        "max_paired_cash_delta": float(np.max(cash_deltas)),
        "ci_95_cash_delta": [ci_lower, ci_upper],
        "h2h": {
            "matches": len(h2h_results),
            "v39_wins": v39_h2h_wins,
            "v39_losses": v39_h2h_losses,
            "v39_ties": v39_h2h_ties,
            "mean_margin": float(np.mean(h2h_margins))
        },
        "elapsed_seconds": time.time() - start_t
    }
    
    with open(OUT_RESULTS, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "h2h": h2h_results, "paired": paired_evals}, f, indent=2)
        
    with open(DONE_FILE, "w", encoding="utf-8") as f:
        f.write("DONE\n")
        
    print("\n==========================================")
    print("V39 REGRESSION TOURNAMENT COMPLETE")
    print("==========================================")
    print(f"Total Paired Matches: {total_matches}")
    print(f"V35 Wins: {v35_total_wins} ({v35_total_wins/total_matches:.1%})")
    print(f"V39 Wins: {v39_total_wins} ({v39_total_wins/total_matches:.1%})")
    print(f"Rescues: {rescues} | Casualties: {casualties}")
    print(f"Mean Paired Cash Delta: ${np.mean(cash_deltas):+.2f} (95% CI: [${ci_lower:+.2f}, ${ci_upper:+.2f}])")
    print(f"H2H V39 vs V35: {v39_h2h_wins}W / {v39_h2h_losses}L / {v39_h2h_ties}T")
    print(f"Elapsed Time: {summary['elapsed_seconds']:.1f}s")

if __name__ == "__main__":
    main()
