import sys
import os
sys.path.insert(0, ".")
import json
import time
import math
import numpy as np
import scipy.stats as stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as v1
import opponents.live_flooder_v1 as flooder
import scratch.closed_loop_arch_v1 as cl_arch

DEV_SEEDS = [10000 + i * 37 for i in range(100)] # 100 seeds x 2 seats = 200 matches
HOLDOUT_SEEDS = [70000 + i * 41 for i in range(100)] # 100 unseen seeds x 2 seats = 200 matches


def run_single_game(args):
    cand_factory_name, opp_factory_name, seed, p0_is_cand = args
    
    # Instantiate agents
    if cand_factory_name == "CL_ARCH":
        cand_inst = cl_arch.ClosedLoopArchAgent()
        cand_agent = lambda obs, cfg=None: cand_inst(obs, cfg)
    else:
        cand_agent = v2.agent
        
    if opp_factory_name == "V2":
        opp_agent = v2.agent
    elif opp_factory_name == "V1":
        opp_agent = v1.agent
    elif opp_factory_name == "FLOODER":
        opp_agent = flooder.agent
    else:
        opp_agent = v2.agent
        
    pair = [cand_agent, opp_agent] if p0_is_cand else [opp_agent, cand_agent]
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.run(pair)
    
    cand_idx = 0 if p0_is_cand else 1
    opp_idx = 1 - cand_idx
    
    cand_score = float(env.steps[-1][cand_idx]["reward"] or 0)
    opp_score = float(env.steps[-1][opp_idx]["reward"] or 0)
    margin = cand_score - opp_score
    win = 1.0 if cand_score > opp_score else (0.5 if cand_score == opp_score else 0.0)
    
    obs_cand = env.steps[-1][cand_idx]["observation"]
    farm_cand = obs_cand["farms"][cand_idx]
    tiles_cand = farm_cand["tiles"]
    
    pastures = sum(1 for row in tiles_cand for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    cows = sum(1 for row in tiles_cand for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    sheep = sum(1 for row in tiles_cand for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
    quads = len(farm_cand.get("unlocked_quadrants", []))
    
    return {
        "seed": seed,
        "seat": "P0" if p0_is_cand else "P1",
        "cand_score": cand_score,
        "opp_score": opp_score,
        "margin": margin,
        "win": win,
        "pastures": pastures,
        "cows": cows,
        "sheep": sheep,
        "quads": quads
    }


def evaluate_suite(seeds, opp_name="V2", max_workers=10):
    tasks = []
    for s in seeds:
        tasks.append(("CL_ARCH", opp_name, s, True))  # P0
        tasks.append(("CL_ARCH", opp_name, s, False)) # P1
        
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_game, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())
            
    scores_cand = [r["cand_score"] for r in results]
    scores_opp = [r["opp_score"] for r in results]
    margins = [r["margin"] for r in results]
    wins = [r["win"] for r in results]
    
    mean_cand = float(np.mean(scores_cand))
    mean_opp = float(np.mean(scores_opp))
    mean_margin = float(np.mean(margins))
    median_margin = float(np.median(margins))
    p5_margin = float(np.percentile(margins, 5))
    worst_loss = float(np.min(margins))
    win_rate = float(np.mean(wins))
    std_margin = float(np.std(margins))
    sem_margin = float(stats.sem(margins))
    ci_95 = float(1.96 * sem_margin)
    catastrophic_rate = float(sum(1 for m in margins if m < -50000) / len(margins))
    
    # Paired t-test
    t_stat, p_val = stats.ttest_1samp(margins, 0.0)
    
    return {
        "n_matches": len(results),
        "mean_cand": mean_cand,
        "mean_opp": mean_opp,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "p5_margin": p5_margin,
        "worst_loss": worst_loss,
        "win_rate": win_rate,
        "std_margin": std_margin,
        "ci_95": ci_95,
        "p_val": float(p_val),
        "catastrophic_rate": catastrophic_rate,
        "raw_results": results
    }


if __name__ == "__main__":
    print("="*80)
    print("RUNNING CLOSED-LOOP ARCHITECTURE EVALUATION (DEV + HOLDOUT + OPPONENTS)")
    print("="*80)
    
    start_t = time.time()
    
    # 1. Development Suite vs Frozen V2 (200 matches)
    print("\n[1/4] Running Development Suite vs Frozen V2 (N=200 matches)...")
    dev_res = evaluate_suite(DEV_SEEDS, opp_name="V2")
    print(f"  Dev vs V2: Score ${dev_res['mean_cand']:,.1f} vs V2 ${dev_res['mean_opp']:,.1f} | Margin ${dev_res['mean_margin']:+,.1f} +/- ${dev_res['ci_95']:,.1f} | WR {dev_res['win_rate']*100:.1f}% | p={dev_res['p_val']:.2e}")
    
    # 2. Unseen Holdout Suite vs Frozen V2 (200 matches)
    print("\n[2/4] Running Frozen Unseen Holdout vs Frozen V2 (N=200 matches)...")
    holdout_res = evaluate_suite(HOLDOUT_SEEDS, opp_name="V2")
    print(f"  Holdout vs V2: Score ${holdout_res['mean_cand']:,.1f} vs V2 ${holdout_res['mean_opp']:,.1f} | Margin ${holdout_res['mean_margin']:+,.1f} +/- ${holdout_res['ci_95']:,.1f} | WR {holdout_res['win_rate']*100:.1f}% | p={holdout_res['p_val']:.2e}")
    
    # 3. Development vs Aethel V1 (100 matches)
    print("\n[3/4] Running Development vs Aethel V1 (N=100 matches)...")
    v1_res = evaluate_suite(DEV_SEEDS[:50], opp_name="V1")
    print(f"  Dev vs V1: Score ${v1_res['mean_cand']:,.1f} vs V1 ${v1_res['mean_opp']:,.1f} | Margin ${v1_res['mean_margin']:+,.1f} +/- ${v1_res['ci_95']:,.1f} | WR {v1_res['win_rate']*100:.1f}% | p={v1_res['p_val']:.2e}")

    # 4. Development vs Live Flooder (100 matches)
    print("\n[4/4] Running Development vs Live Flooder (N=100 matches)...")
    flooder_res = evaluate_suite(DEV_SEEDS[:50], opp_name="FLOODER")
    print(f"  Dev vs Flooder: Score ${flooder_res['mean_cand']:,.1f} vs Flooder ${flooder_res['mean_opp']:,.1f} | Margin ${flooder_res['mean_margin']:+,.1f} +/- ${flooder_res['ci_95']:,.1f} | WR {flooder_res['win_rate']*100:.1f}% | p={flooder_res['p_val']:.2e}")

    summary_data = {
        "dev_vs_v2": dev_res,
        "holdout_vs_v2": holdout_res,
        "dev_vs_v1": v1_res,
        "dev_vs_flooder": flooder_res,
        "elapsed_seconds": time.time() - start_t
    }
    
    with open("scratch/closed_loop_evaluation_summary.json", "w") as f:
        json.dump(summary_data, f, indent=2)
        
    print(f"\nAll evaluations complete in {time.time() - start_t:.1f}s. Saved to scratch/closed_loop_evaluation_summary.json")
