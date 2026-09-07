"""
Fast Parallel Worker-Level Forensic Instrumentation & Decomposition
===================================================================
Uses ProcessPoolExecutor to rapidly instrument Frozen V2 and CL-Commitment-V1.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_v1_agent

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _quad(x, y):
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def _run_single_forensic_seed(item):
    agent_path, seed = item
    if agent_path == "v2":
        agent_fn = v2_agent
    else:
        agent_fn = comm_v1_agent
        
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    movement_categories = defaultdict(int)
    total_moves = 0
    total_prod = 0
    total_idle = 0
    
    worker_last_prod_pos = {}
    worker_last_prod_step = {}
    worker_consec_switches = defaultdict(int)
    
    shed_visits_payloads = []
    shed_visit_reasons = defaultdict(int)
    
    pairwise_crossings = 0
    pairwise_target_distances = []
    consecutive_task_manhattan = []
    
    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx-1][0]['observation']
        curr_obs = steps[s_idx][0]['observation']
        
        prev_farm = prev_obs['farms'][0]
        curr_farm = curr_obs['farms'][0]
        
        prev_workers = [tuple(prev_farm['farmer'])] + [tuple(h) for h in prev_farm['hands']]
        curr_workers = [tuple(curr_farm['farmer'])] + [tuple(h) for h in curr_farm['hands']]
        
        curr_invs = curr_obs.get('private', {}).get('inventories', []) or []
        curr_invs = list(curr_invs) + [{} for _ in range(len(curr_workers) - len(curr_invs))]
        
        n_w = min(len(prev_workers), len(curr_workers))
        step_targets = []
        
        for w_idx in range(n_w):
            p0 = prev_workers[w_idx]
            p1 = curr_workers[w_idx]
            inv = curr_invs[w_idx]
            
            load = sum(int(v or 0) for k, v in inv.items() if k not in ("COW", "SHEEP"))
            q0 = _quad(p0[0], p0[1])
            q1 = _quad(p1[0], p1[1])
            
            t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < BOARD and 0 <= p0[0] < BOARD else None
            t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < BOARD and 0 <= p0[0] < BOARD else None
            
            is_move = (p0 != p1)
            is_prod = False
            if not is_move:
                if t_prev != t_curr or p0 in SHED_ACCESS or p0 in WELL_ACCESS:
                    is_prod = True
            
            if is_move:
                total_moves += 1
                step_targets.append(p1)
                
                if p1 in SHED_ACCESS and p0 not in SHED_ACCESS:
                    movement_categories['6_toward_shed'] += 1
                    shed_visits_payloads.append(load)
                    if load >= 4:
                        shed_visit_reasons['high_load_drop'] += 1
                    elif load in (1, 2, 3):
                        shed_visit_reasons['fragmented_low_load_drop'] += 1
                    elif int(inv.get('WHEAT', 0) or 0) > 0:
                        shed_visit_reasons['wheat_feed_transit'] += 1
                    else:
                        shed_visit_reasons['empty_pass_through'] += 1
                elif p0 in SHED_ACCESS and p1 not in SHED_ACCESS:
                    movement_categories['7_away_from_shed'] += 1
                elif p1 in WELL_ACCESS:
                    movement_categories['8_resource_pickup'] += 1
                elif q0 != q1:
                    movement_categories['5_zone_switch_crossing'] += 1
                    worker_consec_switches[w_idx] += 1
                elif _dist(p0, p1) == 1:
                    if w_idx in worker_last_prod_step and (s_idx - worker_last_prod_step[w_idx] == 1):
                        movement_categories['2_corridor_sweep'] += 1
                    else:
                        movement_categories['1_move_toward_target'] += 1
                else:
                    movement_categories['4_task_reassignment_drift'] += 1
            elif is_prod:
                total_prod += 1
                if w_idx in worker_last_prod_pos:
                    lp = worker_last_prod_pos[w_idx]
                    consecutive_task_manhattan.append(_dist(lp, p0))
                worker_last_prod_pos[w_idx] = p0
                worker_last_prod_step[w_idx] = s_idx
            else:
                total_idle += 1
                movement_categories['10_idle_wait'] += 1
        
        for i in range(len(step_targets)):
            for j in range(i + 1, len(step_targets)):
                pt_i = step_targets[i]
                pt_j = step_targets[j]
                d_ij = _dist(pt_i, pt_j)
                pairwise_target_distances.append(d_ij)
                w_i_p0 = prev_workers[i]
                w_j_p0 = prev_workers[j]
                if (pt_i[0] - pt_j[0]) * (w_i_p0[0] - w_j_p0[0]) < 0:
                    pairwise_crossings += 1
                    
    return {
        "agent": agent_path,
        "seed": seed,
        "reward": float(steps[-1][0].reward or 0.0),
        "moves": total_moves,
        "prod": total_prod,
        "idle": total_idle,
        "categories": dict(movement_categories),
        "mean_consec_manhattan": float(np.mean(consecutive_task_manhattan)) if consecutive_task_manhattan else 0.0,
        "pct_1step_consec": float(np.mean([1 if d == 1 else 0 for d in consecutive_task_manhattan]) * 100) if consecutive_task_manhattan else 0.0,
        "pct_2step_consec": float(np.mean([1 if d <= 2 else 0 for d in consecutive_task_manhattan]) * 100) if consecutive_task_manhattan else 0.0,
        "shed_visits": len(shed_visits_payloads),
        "shed_payloads": shed_visits_payloads,
        "shed_reasons": dict(shed_visit_reasons),
        "pairwise_crossings": pairwise_crossings,
        "mean_pairwise_target_dist": float(np.mean(pairwise_target_distances)) if pairwise_target_distances else 0.0
    }

def run_parallel_forensics(seeds, max_workers=10):
    tasks = []
    for s in seeds:
        tasks.append(("v2", s))
        tasks.append(("cl", s))
        
    v2_results = []
    cl_results = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_forensic_seed, t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            if res["agent"] == "v2":
                v2_results.append(res)
            else:
                cl_results.append(res)
                
    return v2_results, cl_results

if __name__ == "__main__":
    seeds = [42] + list(range(1000, 1030))
    print(f"Running Parallel Forensics on {len(seeds)} matched seeds across CPU cores...")
    v2_res, cl_res = run_parallel_forensics(seeds, max_workers=10)
    
    with open("scratch/parallel_forensic_results.json", "w") as f:
        json.dump({"v2": v2_res, "cl": cl_res}, f, indent=2)
    print("Forensic analysis complete! Written to scratch/parallel_forensic_results.json")
