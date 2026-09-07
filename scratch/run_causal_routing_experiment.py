import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent
from candidates.candidate_cl_aethel_prime import agent as prime_agent
import numpy as np
import json

SEEDS = [42, 101, 215, 333, 404, 505, 606, 707, 808, 909]

def run_causal_arms():
    print("=================================================================")
    print(f"PHASE 11 & 12: CAUSAL ROUTING & ECONOMIC ABLATIONS ({len(SEEDS)} seeds)")
    print("=================================================================")
    
    arms = {
        "A_Frozen_V2": v2_mod.agent,
        "B_Grandmaster": gm_agent,
        "C_Prime": prime_agent,
        "D_CL_Execution_V1": cl_v1_agent,
    }
    
    results = {}
    for arm_name, agent_fn in arms.items():
        rewards = []
        prod_list = []
        move_list = []
        idle_list = []
        
        for s in SEEDS:
            p_cnt, m_cnt, i_cnt = 0, 0, 0
            def wrapped(obs, config=None):
                nonlocal p_cnt, m_cnt, i_cnt
                act = agent_fn(obs, config) if config else agent_fn(obs)
                all_ops = []
                f = act.get("farmer")
                if f: all_ops.append(f[0] if isinstance(f, list) and f else str(f))
                for h in act.get("hands", []) or []:
                    if h: all_ops.append(h[0] if isinstance(h, list) and h else str(h))
                for op in all_ops:
                    if op in ("NORTH", "SOUTH", "EAST", "WEST"): m_cnt += 1
                    elif op in ("PASS", "NONE", ""): i_cnt += 1
                    else: p_cnt += 1
                return act
                
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
            env.run([wrapped, "starter"])
            r = env.steps[-1][0]["reward"]
            rewards.append(r)
            prod_list.append(p_cnt)
            move_list.append(m_cnt)
            idle_list.append(i_cnt)
            
        results[arm_name] = {
            "reward_mean": float(np.mean(rewards)),
            "reward_std": float(np.std(rewards)),
            "reward_raw": rewards,
            "prod_mean": float(np.mean(prod_list)),
            "move_mean": float(np.mean(move_list)),
            "idle_mean": float(np.mean(idle_list)),
        }
        print(f"Arm {arm_name:<18}: Reward = ${results[arm_name]['reward_mean']:>10.2f} +/- ${results[arm_name]['reward_std']:>8.2f} | Prod = {results[arm_name]['prod_mean']:>6.1f} | Move = {results[arm_name]['move_mean']:>6.1f} | Idle = {results[arm_name]['idle_mean']:>6.1f}")
        
    with open('scratch/causal_routing_experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved causal results to scratch/causal_routing_experiment_results.json")

if __name__ == "__main__":
    run_causal_arms()
