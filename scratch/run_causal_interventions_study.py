"""
100-Seed Matched Screening & Causal Attribution Study for Interventions 1-7
===========================================================================
Evaluates Frozen V2, CL-Commitment-V1, and Arms 1-7 across 100 matched seeds (1000-1099).
Collects full movement efficiency, productive capacity, and economic reward telemetry.
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
from scratch.build_isolated_interventions import (
    Arm1_SoftOwnership, Arm2_JointAllocation, Arm3_ClusterLock,
    Arm4_ZoneExitPenalty, Arm5_ShedOpportunism, Arm7_Prepositioning,
    SHED_ACCESS, WELL_ACCESS, _dist, _quad
)

# Instantiate agents
_ARM1 = Arm1_SoftOwnership()
def agent_arm1(obs, config=None): return _ARM1(obs, config)

_ARM2 = Arm2_JointAllocation()
def agent_arm2(obs, config=None): return _ARM2(obs, config)

_ARM3 = Arm3_ClusterLock()
def agent_arm3(obs, config=None): return _ARM3(obs, config)

_ARM4 = Arm4_ZoneExitPenalty()
def agent_arm4(obs, config=None): return _ARM4(obs, config)

_ARM5 = Arm5_ShedOpportunism()
def agent_arm5(obs, config=None): return _ARM5(obs, config)

_ARM7 = Arm7_Prepositioning()
def agent_arm7(obs, config=None): return _ARM7(obs, config)

AGENT_MAP = {
    "V2": v2_agent,
    "CL_V1": comm_v1_agent,
    "Arm1_SoftOwnership": agent_arm1,
    "Arm2_JointAllocation": agent_arm2,
    "Arm3_ClusterLock": agent_arm3,
    "Arm4_ZoneExitPenalty": agent_arm4,
    "Arm5_ShedOpportunism": agent_arm5,
    "Arm7_Prepositioning": agent_arm7,
}

def _eval_single_match(item):
    arm_name, seed = item
    agent_fn = AGENT_MAP[arm_name]
    
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    
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
        "arm": arm_name,
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

def run_study(seeds, arms=None, max_workers=10):
    if arms is None:
        arms = list(AGENT_MAP.keys())
    tasks = [(arm, s) for arm in arms for s in seeds]
    results_by_arm = defaultdict(list)
    
    print(f"Executing {len(tasks)} total matches across {len(seeds)} seeds and {len(arms)} arms...")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_eval_single_match, t) for t in tasks]
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results_by_arm[res["arm"]].append(res)
            completed += 1
            if completed % max(1, len(tasks) // 10) == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} matches ({completed/len(tasks)*100:.1f}%)")
                
    return results_by_arm

if __name__ == "__main__":
    seeds = list(range(1000, 1100)) # 100 matched seeds
    res = run_study(seeds, max_workers=12)
    
    summary = {}
    print("\n" + "=" * 90)
    print(f"{'ARM':<22} | {'REWARD (MEAN±STD)':<20} | {'PROD':<7} | {'MOVES':<7} | {'IDLE':<6} | {'LEG':<5} | {'1-STEP%':<7} | {'SHED':<6} | {'PROD/MOV'}")
    print("=" * 90)
    
    for arm, list_m in res.items():
        r_arr = [m["reward"] for m in list_m]
        p_arr = [m["prod"] for m in list_m]
        m_arr = [m["moves"] for m in list_m]
        i_arr = [m["idle"] for m in list_m]
        l_arr = [m["mean_leg"] for m in list_m]
        s1_arr = [m["pct_1step"] for m in list_m]
        sh_arr = [m["shed_visits"] for m in list_m]
        pm_arr = [m["prod_move_ratio"] for m in list_m]
        
        summary[arm] = {
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
        
        print(f"{arm:<22} | ${np.mean(r_arr):9.1f} ± ${np.std(r_arr):7.1f} | {np.mean(p_arr):7.1f} | {np.mean(m_arr):7.1f} | {np.mean(i_arr):6.1f} | {np.mean(l_arr):5.2f} | {np.mean(s1_arr):6.1f}% | {np.mean(sh_arr):6.1f} | {np.mean(pm_arr):.3f}")
        
    print("=" * 90)
    with open("scratch/causal_interventions_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Causal study complete! Results written to scratch/causal_interventions_summary.json")
