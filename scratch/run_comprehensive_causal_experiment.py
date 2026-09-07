import sys, os
sys.path.insert(0, os.path.abspath('.'))
import copy
import json
import kaggle_environments
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent, CLAethelGrandmaster, _bfs

SEEDS = [42, 100, 2024, 104816794, 104817623]

# Arm D: Hybrid - Prime Scheduler (using naive closest target instead of zoned sweep)
class HybridMinusPrimeScheduler(CLAethelGrandmaster):
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        actions = [None] * len(all_workers)
        claimed = set()
        ns = (4, 4)
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            load = sum(int(inv.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER"))
            x, y = pos
            t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
            if pos in ((4,4),(5,4),(4,5),(5,5)) and load > 0:
                actions[i] = ["DROP"]
                claimed.add(pos)
            elif isinstance(t, dict) and t.get("kind") == "PLANT" and int(t.get("yield_units", 0) or 0) > 0 and pos in scan_res["ripe_crops"]:
                actions[i] = ["HARVEST"]
                claimed.add(pos)
            elif isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today"):
                actions[i] = ["WATER"]
                claimed.add(pos)
            else:
                # Naive closest target
                all_targets = scan_res["urgent_unwatered"] + scan_res["unwatered"] + scan_res["ripe_crops"] + scan_res["unbuilt_p"]
                cands = [tgt for tgt in all_targets if tgt not in claimed]
                if cands:
                    tgt = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))
                    claimed.add(tgt)
                    actions[i] = [_bfs(pos, tgt, tiles)]
                else:
                    actions[i] = ["PASS"]
        return actions

# Arm E: Hybrid - V2 Economic Features (Cap hiring to 4 hands, no midgame melons)
class HybridMinusV2Econ(CLAethelGrandmaster):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Suppress midgame melons
        orders = [o for o in orders if not (isinstance(o, list) and o and o[0] == "BUY_SEED" and o[1] == "MELON" and day >= 10)]
        # Cap hiring to 4
        orders = [o for o in orders if not (isinstance(o, list) and o and o[0] == "HIRE" and hired >= 4)]
        return orders[:10]

# Arm F: Hybrid - Dynamic Policy Layer (Fixed day-based actions without checking cash/obs)
class HybridMinusDynamicPolicy(CLAethelGrandmaster):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []
        if step == 0:
            return [["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1], ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 10], ["BUY_PRODUCT", "WHEAT", 17], ["HIRE"], ["HIRE"]]
        # Fixed sells without gross-impact ranking
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY"):
            qty = int(shed.get(item, 0) or 0)
            if qty > 0 and len(orders) < 8:
                orders.append(["SELL", item, qty])
        return orders[:10]

arm_d_inst = HybridMinusPrimeScheduler()
def arm_d_agent(obs, cfg=None): return arm_d_inst(obs, cfg)

arm_e_inst = HybridMinusV2Econ()
def arm_e_agent(obs, cfg=None): return arm_e_inst(obs, cfg)

arm_f_inst = HybridMinusDynamicPolicy()
def arm_f_agent(obs, cfg=None): return arm_f_inst(obs, cfg)

ARMS = [
    ("Arm A: Frozen V2", v2_mod.agent),
    ("Arm B: CL-Aethel Prime", prime_agent),
    ("Arm C: CL-Aethel Grandmaster", gm_agent),
    ("Arm D: Hybrid - Prime Scheduler", arm_d_agent),
    ("Arm E: Hybrid - V2 Econ Features", arm_e_agent),
    ("Arm F: Hybrid - Dynamic Policy", arm_f_agent),
]

def run_multi_arm_experiment():
    print("="*90)
    print(f"PHASE 9: COMPREHENSIVE CAUSAL MULTI-ARM EXPERIMENT ({len(SEEDS)} MATCHED SEEDS)")
    print("="*90)
    
    results = {}
    
    for arm_name, arm_agent in ARMS:
        print(f"\nEvaluating {arm_name}...")
        scores = []
        prod_actions_list = []
        move_actions_list = []
        
        for s in SEEDS:
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
            starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
            env.run([arm_agent, starter])
            
            reward = env.steps[-1][0]["reward"]
            scores.append(reward)
            
            # Count actions
            prod = 0
            move = 0
            for step_data in env.steps[1:]:
                act = step_data[0].get("action") or {}
                units = [act.get("farmer", ["PASS"])] + (act.get("hands", []) if isinstance(act, dict) else [])
                for u in units:
                    if not u: continue
                    op = u[0] if isinstance(u, (list, tuple)) else str(u)
                    if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                        move += 1
                    elif op != "PASS":
                        prod += 1
            prod_actions_list.append(prod)
            move_actions_list.append(move)
            print(f"  Seed {s:9d}: Reward = ${reward:>10,.1f} | Prod = {prod} | Move = {move}")
            
        mean_r = float(np.mean(scores))
        std_r = float(np.std(scores))
        mean_prod = float(np.mean(prod_actions_list))
        mean_move = float(np.mean(move_actions_list))
        
        results[arm_name] = {
            "mean_reward": mean_r,
            "std_reward": std_r,
            "scores": scores,
            "mean_prod_actions": mean_prod,
            "mean_move_actions": mean_move
        }
        
    print("\n" + "="*90)
    print("CAUSAL MULTI-ARM SUMMARY TABLE")
    print("="*90)
    baseline_v2 = results["Arm A: Frozen V2"]["mean_reward"]
    prime_base = results["Arm B: CL-Aethel Prime"]["mean_reward"]
    gm_score = results["Arm C: CL-Aethel Grandmaster"]["mean_reward"]
    
    for arm_name, data in results.items():
        r = data["mean_reward"]
        std = data["std_reward"]
        d_v2 = r - baseline_v2
        d_prime = r - prime_base
        prod = data["mean_prod_actions"]
        print(f"  {arm_name:<34}: ${r:>10,.1f} +/- {std:>7,.1f} | vs V2: ${d_v2:>+10,.1f} | vs Prime: ${d_prime:>+10,.1f} | Prod: {prod:>5.0f}")
        
    with open("scratch/causal_multi_arm_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved multi-arm results to scratch/causal_multi_arm_results.json")

if __name__ == '__main__':
    run_multi_arm_experiment()
