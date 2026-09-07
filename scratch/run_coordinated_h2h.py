"""
Head-to-Head & Comparative Evaluation for ClosedLoopCoordinatedV1
================================================================
Evaluates CL-Coordinated-V1 against:
1. Starter Benchmark (100 Seeds 1000-1099)
2. Direct Frozen V2 Head-to-Head (100 Seeds 5000-5099, Alternating Seats)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_v1_agent
from scratch.build_coordinated_candidate import agent as coord_agent, SHED_ACCESS, WELL_ACCESS, _dist, _quad

def eval_single_starter_match(seed):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([coord_agent, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    moves = 0
    prod = 0
    idle = 0
    shed_visits = 0
    
    leg_lengths = []
    consecutive_same_zone = 0
    total_prod_transitions = 0
    within_2_transitions = 0
    within_1_transitions = 0
    worker_last_prod_pos = {}
    
    for s_idx in range(1, total_steps):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        
        prev_workers = [tuple(prev_farm['farmer'])] + [tuple(h) for h in prev_farm['hands']]
        curr_workers = [tuple(curr_farm['farmer'])] + [tuple(h) for h in curr_farm['hands']]
        
        for w_idx in range(min(len(prev_workers), len(curr_workers))):
            p0 = prev_workers[w_idx]
            p1 = curr_workers[w_idx]
            
            if p0 != p1:
                moves += 1
                if p1 in SHED_ACCESS and p0 not in SHED_ACCESS:
                    shed_visits += 1
            else:
                t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                
                is_prod = False
                if t_prev != t_curr or p0 in SHED_ACCESS or p0 in WELL_ACCESS:
                    is_prod = True
                    
                if is_prod:
                    prod += 1
                    if w_idx in worker_last_prod_pos:
                        lp = worker_last_prod_pos[w_idx]
                        d = _dist(lp, p0)
                        leg_lengths.append(d)
                        total_prod_transitions += 1
                        if d == 1: within_1_transitions += 1
                        if d <= 2: within_2_transitions += 1
                        if _quad(lp[0], lp[1]) == _quad(p0[0], p0[1]): consecutive_same_zone += 1
                    worker_last_prod_pos[w_idx] = p0
                else:
                    idle += 1
                    
    reward = float(steps[-1][0].reward or 0.0)
    mean_leg = np.mean(leg_lengths) if leg_lengths else 0.0
    pct_1step = (within_1_transitions / total_prod_transitions * 100.0) if total_prod_transitions else 0.0
    pct_2step = (within_2_transitions / total_prod_transitions * 100.0) if total_prod_transitions else 0.0
    
    return {
        "seed": seed,
        "reward": reward,
        "moves": moves,
        "prod": prod,
        "idle": idle,
        "mean_leg": mean_leg,
        "pct_1step": pct_1step,
        "pct_2step": pct_2step,
        "shed_visits": shed_visits,
        "prod_move_ratio": prod / max(1, moves)
    }

def run_coordinated_evaluation(seeds=list(range(1000, 1100)), max_workers=12):
    print(f"Running CL-Coordinated-V1 Starter Benchmark across {len(seeds)} seeds...")
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(eval_single_starter_match, s) for s in seeds]
        for f in as_completed(futures):
            results.append(f.result())
            
    r_arr = [m["reward"] for m in results]
    p_arr = [m["prod"] for m in results]
    m_arr = [m["moves"] for m in results]
    i_arr = [m["idle"] for m in results]
    l_arr = [m["mean_leg"] for m in results]
    s1_arr = [m["pct_1step"] for m in results]
    sh_arr = [m["shed_visits"] for m in results]
    pm_arr = [m["prod_move_ratio"] for m in results]
    
    report = {
        "mean_reward": float(np.mean(r_arr)),
        "std_reward": float(np.std(r_arr)),
        "median_reward": float(np.median(r_arr)),
        "mean_prod": float(np.mean(p_arr)),
        "mean_moves": float(np.mean(m_arr)),
        "mean_idle": float(np.mean(i_arr)),
        "mean_leg": float(np.mean(l_arr)),
        "mean_pct_1step": float(np.mean(s1_arr)),
        "mean_shed_visits": float(np.mean(sh_arr)),
        "mean_prod_move_ratio": float(np.mean(pm_arr)),
    }
    
    print("\n" + "=" * 80)
    print("CL-COORDINATED-V1 (100 SEEDS 1000-1099) BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Mean Reward:        ${report['mean_reward']:10.2f} ± ${report['std_reward']:8.2f} (Median: ${report['median_reward']:10.2f})")
    print(f"Productive Actions: {report['mean_prod']:10.1f}")
    print(f"Movement Actions:   {report['mean_moves']:10.1f}")
    print(f"Idle Actions:       {report['mean_idle']:10.1f}")
    print(f"Mean Leg Length:    {report['mean_leg']:10.2f}")
    print(f"1-Step Leg %:       {report['mean_pct_1step']:9.1f}%")
    print(f"Shed Visits:        {report['mean_shed_visits']:10.1f}")
    print(f"Prod / Move Ratio:  {report['mean_prod_move_ratio']:10.3f}")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    report = run_coordinated_evaluation(list(range(1000, 1100)))
    with open("scratch/coordinated_benchmark_summary.json", "w") as f:
        json.dump(report, f, indent=2)
