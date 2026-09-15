"""
Head-to-Head Tournament against Frozen V2
Runs 100 Matched Games (Seeds 5000-5099) with Strict Seat Alternation:
- 50 games with Challenger as Player 0 (Starter as Player 1)
- 50 games with Challenger as Player 1 (Starter as Player 0)
Calculates:
- Wins, Losses, Ties
- Mean Candidate Cash, Mean V2 Cash, Mean Margin, Median Margin
- 95% Confidence Interval, Effect Size
"""

import sys
import time
import numpy as np
from kaggle_environments import make
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_h2h_match(args):
    cand_path, v2_path, seed, cand_seat = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    if cand_seat == 0:
        env.run([cand_path, v2_path])
        cand_idx, v2_idx = 0, 1
    else:
        env.run([v2_path, cand_path])
        cand_idx, v2_idx = 1, 0
        
    cand_reward = float(env.steps[-1][cand_idx].get("reward", 0.0) or 0.0)
    v2_reward = float(env.steps[-1][v2_idx].get("reward", 0.0) or 0.0)
    margin = cand_reward - v2_reward
    
    return seed, cand_seat, cand_reward, v2_reward, margin

def run_tournament(cand_name, cand_path, v2_path="candidates/slot2_aethel_refined_v2.py", n_games=100):
    seeds = list(range(5000, 5000 + n_games))
    tasks = []
    for i, s in enumerate(seeds):
        seat = 0 if (i % 2 == 0) else 1
        tasks.append((cand_path, v2_path, s, seat))
        
    print(f"Starting {n_games}-Match H2H Tournament: {cand_name} vs Frozen V2...")
    t0 = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(run_h2h_match, t) for t in tasks]
        for f in as_completed(futs):
            results.append(f.result())
            
    cand_rewards = [r[2] for r in results]
    v2_rewards = [r[3] for r in results]
    margins = [r[4] for r in results]
    
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)
    ties = sum(1 for m in margins if m == 0)
    
    mean_margin = float(np.mean(margins))
    std_margin = float(np.std(margins))
    ci95_margin = 1.96 * std_margin / np.sqrt(len(margins))
    
    print("\n" + "=" * 65)
    print(f"HEAD-TO-HEAD TOURNAMENT RESULTS: {cand_name} vs Frozen V2")
    print("=" * 65)
    print(f"Matches Played:  {len(results)} (Alternating Seats)")
    print(f"Record (W-L-T):  {wins} - {losses} - {ties} (Win Rate: {wins/len(results)*100:.1f}%)")
    print(f"Candidate Cash:  ${np.mean(cand_rewards):10.2f} ± ${np.std(cand_rewards):8.2f}")
    print(f"Frozen V2 Cash:  ${np.mean(v2_rewards):10.2f} ± ${np.std(v2_rewards):8.2f}")
    print(f"Mean Net Margin: ${mean_margin:10.2f} ± ${ci95_margin:8.2f}")
    print(f"Median Margin:   ${np.median(margins):10.2f}")
    print(f"Elapsed Time:    {time.time()-t0:.1f}s")
    print("=" * 65)

if __name__ == "__main__":
    cand_path = sys.argv[1] if len(sys.argv) > 1 else "candidates/candidate_cl_economic_v1.py"
    cand_name = sys.argv[2] if len(sys.argv) > 2 else "Candidate"
    run_tournament(cand_name, cand_path)
