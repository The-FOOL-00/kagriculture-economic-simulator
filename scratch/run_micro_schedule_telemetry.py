import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent
from collections import defaultdict, Counter
import json
import numpy as np

SEEDS = [42, 101, 215, 333, 555]

def profile_agent_telemetry(name, agent_fn):
    print(f"\n=======================================================")
    print(f"PROFILING TELEMETRY: {name}")
    print(f"=======================================================")
    
    all_metrics = {
        "reward": [],
        "prod": [],
        "move": [],
        "idle": [],
        "leg_mean": [],
        "leg_1_pct": [],
        "leg_le2_pct": [],
        "crops": [],
        "livestock": [],
        "milk": [],
        "wool": [],
        "melon": [],
        "strawberry": [],
        "wheat": []
    }
    
    for s in SEEDS:
        prod_count = 0
        move_count = 0
        idle_count = 0
        move_streaks = defaultdict(list)
        cur_streak = defaultdict(int)
        
        def wrapped_agent(obs, config=None):
            nonlocal prod_count, move_count, idle_count
            act = agent_fn(obs, config) if config else agent_fn(obs)
            all_ops = []
            f_act = act.get("farmer")
            if f_act: all_ops.append(f_act[0] if isinstance(f_act, list) and f_act else str(f_act))
            for h in act.get("hands", []) or []:
                if h: all_ops.append(h[0] if isinstance(h, list) and h else str(h))
                
            for w_idx, op in enumerate(all_ops):
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    move_count += 1
                    cur_streak[w_idx] += 1
                elif op in ("PASS", "NONE", ""):
                    idle_count += 1
                else:
                    prod_count += 1
                    if cur_streak[w_idx] > 0:
                        move_streaks[w_idx].append(cur_streak[w_idx])
                        cur_streak[w_idx] = 0
            return act

        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env.run([wrapped_agent, "starter"])
        
        final_step = env.steps[-1]
        r = final_step[0]["reward"]
        
        # Calculate leg statistics
        all_streaks = [st for streaks in move_streaks.values() for st in streaks]
        leg_m = np.mean(all_streaks) if all_streaks else 0.0
        leg_1 = sum(1 for st in all_streaks if st == 1) / max(1, len(all_streaks)) * 100
        leg_le2 = sum(1 for st in all_streaks if st <= 2) / max(1, len(all_streaks)) * 100
        
        all_metrics["reward"].append(r)
        all_metrics["prod"].append(prod_count)
        all_metrics["move"].append(move_count)
        all_metrics["idle"].append(idle_count)
        all_metrics["leg_mean"].append(leg_m)
        all_metrics["leg_1_pct"].append(leg_1)
        all_metrics["leg_le2_pct"].append(leg_le2)
        
    summary = {}
    for k, v in all_metrics.items():
        summary[k] = {
            "mean": float(np.mean(v)),
            "std": float(np.std(v)),
            "raw": v
        }
        print(f"  {k:<14}: mean={summary[k]['mean']:>10.2f} +/- {summary[k]['std']:>8.2f}")
    return summary

if __name__ == "__main__":
    results = {}
    results["Frozen_V2"] = profile_agent_telemetry("Frozen V2", v2_mod.agent)
    results["Grandmaster"] = profile_agent_telemetry("Grandmaster", gm_agent)
    results["CL_Execution_V1"] = profile_agent_telemetry("CL-Execution-V1", cl_v1_agent)
    
    with open('scratch/micro_schedule_telemetry_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved full telemetry to scratch/micro_schedule_telemetry_results.json")
