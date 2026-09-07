"""
Audit and Reconcile Telemetry across seeds and horizons.
Analyzes exact action classifications, movement counts, and discrepancies.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import numpy as np
from collections import defaultdict

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_v1_agent

SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def quad(x, y):
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def run_telemetry_match(agent_fn, seed=42, opponent="starter"):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, opponent])
    
    steps = env.steps
    total_steps = len(steps)
    
    moves = 0
    prod = 0
    idle = 0
    
    leg_lengths = []
    consecutive_same_zone = 0
    total_prod_transitions = 0
    within_2_transitions = 0
    within_1_transitions = 0
    
    worker_last_prod_pos = {}
    shed_visits = 0
    
    for s_idx in range(1, total_steps):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        
        prev_farmer = tuple(prev_farm['farmer'])
        prev_hands = [tuple(h) for h in prev_farm['hands']]
        prev_workers = [prev_farmer] + prev_hands
        
        curr_farmer = tuple(curr_farm['farmer'])
        curr_hands = [tuple(h) for h in curr_farm['hands']]
        curr_workers = [curr_farmer] + curr_hands
        
        for w_idx in range(min(len(prev_workers), len(curr_workers))):
            p0 = prev_workers[w_idx]
            p1 = curr_workers[w_idx]
            
            if p0 != p1:
                moves += 1
                if p1 in SHED_ACCESS and p0 not in SHED_ACCESS:
                    shed_visits += 1
            else:
                # evaluate tile state change
                t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                
                # Was it productive?
                is_prod = False
                if t_prev != t_curr:
                    is_prod = True
                elif p0 in SHED_ACCESS or p0 in WELL_ACCESS:
                    is_prod = True
                    
                if is_prod:
                    prod += 1
                    if w_idx in worker_last_prod_pos:
                        lp = worker_last_prod_pos[w_idx]
                        d = dist(lp, p0)
                        leg_lengths.append(d)
                        total_prod_transitions += 1
                        if d == 1:
                            within_1_transitions += 1
                        if d <= 2:
                            within_2_transitions += 1
                        if quad(lp[0], lp[1]) == quad(p0[0], p0[1]):
                            consecutive_same_zone += 1
                    worker_last_prod_pos[w_idx] = p0
                else:
                    idle += 1
                    
    reward = float(steps[-1][0].reward or 0.0)
    
    mean_leg = np.mean(leg_lengths) if leg_lengths else 0.0
    pct_1step = (within_1_transitions / total_prod_transitions * 100.0) if total_prod_transitions else 0.0
    pct_2step = (within_2_transitions / total_prod_transitions * 100.0) if total_prod_transitions else 0.0
    pct_same_zone = (consecutive_same_zone / total_prod_transitions * 100.0) if total_prod_transitions else 0.0
    
    return {
        "reward": reward,
        "moves": moves,
        "prod": prod,
        "idle": idle,
        "mean_leg": mean_leg,
        "pct_1step": pct_1step,
        "pct_2step": pct_2step,
        "pct_same_zone": pct_same_zone,
        "shed_visits": shed_visits,
        "prod_transitions": total_prod_transitions
    }

if __name__ == "__main__":
    print("=== SINGLE SEED (SEED 42) TELEMETRY ===")
    v2_s42 = run_telemetry_match(v2_agent, seed=42)
    cl_s42 = run_telemetry_match(comm_v1_agent, seed=42)
    print(f"Frozen V2:       Reward=${v2_s42['reward']:.1f} | Prod={v2_s42['prod']} | Moves={v2_s42['moves']} | Idle={v2_s42['idle']} | MeanLeg={v2_s42['mean_leg']:.2f} | 1-step={v2_s42['pct_1step']:.1f}% | ShedVisits={v2_s42['shed_visits']}")
    print(f"CL-Commitment-V1:Reward=${cl_s42['reward']:.1f} | Prod={cl_s42['prod']} | Moves={cl_s42['moves']} | Idle={cl_s42['idle']} | MeanLeg={cl_s42['mean_leg']:.2f} | 1-step={cl_s42['pct_1step']:.1f}% | ShedVisits={cl_s42['shed_visits']}")
    print(f"Movement Delta on Seed 42: {cl_s42['moves'] - v2_s42['moves']:+d} moves\n")

    print("=== 20-SEED SAMPLE (SEEDS 1000-1019) TELEMETRY ===")
    v2_list = []
    cl_list = []
    for s in range(1000, 1020):
        v2_m = run_telemetry_match(v2_agent, seed=s)
        cl_m = run_telemetry_match(comm_v1_agent, seed=s)
        v2_list.append(v2_m)
        cl_list.append(cl_m)
        print(f"Seed {s:4d}: V2 Move={v2_m['moves']:4d} Prod={v2_m['prod']:4d} | CL Move={cl_m['moves']:4d} Prod={cl_m['prod']:4d} | Delta Move={cl_m['moves']-v2_m['moves']:+4d}")

    print("\n=== SUMMARY OVER 20 SEEDS ===")
    print(f"V2 Mean:  Reward=${np.mean([m['reward'] for m in v2_list]):.1f} | Prod={np.mean([m['prod'] for m in v2_list]):.1f} | Moves={np.mean([m['moves'] for m in v2_list]):.1f} | Idle={np.mean([m['idle'] for m in v2_list]):.1f} | MeanLeg={np.mean([m['mean_leg'] for m in v2_list]):.2f} | 1-step={np.mean([m['pct_1step'] for m in v2_list]):.1f}% | ShedVisits={np.mean([m['shed_visits'] for m in v2_list]):.1f}")
    print(f"CL Mean:  Reward=${np.mean([m['reward'] for m in cl_list]):.1f} | Prod={np.mean([m['prod'] for m in cl_list]):.1f} | Moves={np.mean([m['moves'] for m in cl_list]):.1f} | Idle={np.mean([m['idle'] for m in cl_list]):.1f} | MeanLeg={np.mean([m['mean_leg'] for m in cl_list]):.2f} | 1-step={np.mean([m['pct_1step'] for m in cl_list]):.1f}% | ShedVisits={np.mean([m['shed_visits'] for m in cl_list]):.1f}")
    print(f"Mean Movement Gap: {np.mean([m['moves'] for m in cl_list]) - np.mean([m['moves'] for m in v2_list]):+.1f} moves")
