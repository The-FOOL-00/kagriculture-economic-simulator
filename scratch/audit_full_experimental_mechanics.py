import sys
import os
sys.path.insert(0, ".")
import json
import copy
import numpy as np
import kaggle_environments

import candidates.slot2_aethel_refined_v2 as v2
import scratch.arch_base as arch

def run_telemetry_match(agent_factory, opp_agent, seed, seat=0):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    
    agent_inst = agent_factory()
    pair = [agent_inst, opp_agent] if seat == 0 else [opp_agent, agent_inst]
    
    trace_log = []
    env.reset()
    
    while not env.done:
        step_num = len(env.steps) - 1
        obs = env.state[seat].observation
        farms = obs.get("farms") or []
        priv = obs.get("private") or {}
        my_farm = farms[seat] if len(farms) > seat else {}
        shed = priv.get("shed") or {}
        seeds = priv.get("seeds") or {}
        
        money_before = float(my_farm.get("money", 0) or 0)
        unlocked_quads = list(my_farm.get("unlocked_quadrants") or [])
        farmer_pos = list(my_farm.get("farmer") or [0, 0])
        hands = list(my_farm.get("hands") or [])
        num_hands = len(hands)
        
        tiles = my_farm.get("tiles") or []
        pastures_built = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
        cows_placed = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_placed = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        crops_planted = {}
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c = t.get("crop")
                    crops_planted[c] = crops_planted.get(c, 0) + 1
        
        actions = []
        for p_idx, p_agent in enumerate(pair):
            p_obs = env.state[p_idx].observation
            act = p_agent(p_obs)
            actions.append(act)
        
        my_action = copy.deepcopy(actions[seat])
        env.step(actions)
        
        next_obs = env.state[seat].observation
        next_farms = next_obs.get("farms") or []
        next_my_farm = next_farms[seat] if len(next_farms) > seat else {}
        next_priv = next_obs.get("private") or {}
        money_after = float(next_my_farm.get("money", 0) or 0)
        
        trace_log.append({
            "step": step_num,
            "money_before": money_before,
            "money_after": money_after,
            "money_delta": money_after - money_before,
            "unlocked_quads": unlocked_quads,
            "farmer_pos": farmer_pos,
            "num_hands": num_hands,
            "pastures_built": pastures_built,
            "cows_placed": cows_placed,
            "sheep_placed": sheep_placed,
            "crops_planted": crops_planted,
            "shed": copy.deepcopy(shed),
            "action": my_action,
            "reward": float(env.state[seat].reward or 0)
        })
    
    final_score = float(env.state[seat].reward or 0)
    opp_score = float(env.state[1 - seat].reward or 0)
    
    return {
        "final_score": final_score,
        "opp_score": opp_score,
        "margin": final_score - opp_score,
        "trace": trace_log
    }

seeds = [101, 102, 103, 104, 215620170]

print("="*80)
print("PHASE 2 & 3: RUNNING DETERMINISTIC TELEMETRY MATCHES")
print("="*80)

for s in seeds:
    full_flags = {f"T{i}": True for i in range(1, 9)}
    res_arch = run_telemetry_match(lambda: arch.ArchBaseAgent(full_flags), v2.agent, s, seat=0)
    res_v2 = run_telemetry_match(lambda: v2.agent, v2.agent, s, seat=0)
    
    print(f"Seed {s:10d} | FULL_ARCH (as-is): ${res_arch['final_score']:10,.1f} | V2 Baseline: ${res_v2['final_score']:10,.1f} | Delta: ${res_arch['final_score'] - res_v2['final_score']:10,.1f}")

# Save detailed trace for Seed 215620170 and Seed 101
full_flags = {f"T{i}": True for i in range(1, 9)}
res_arch_215 = run_telemetry_match(lambda: arch.ArchBaseAgent(full_flags), v2.agent, 215620170, seat=0)
res_v2_215 = run_telemetry_match(lambda: v2.agent, v2.agent, 215620170, seat=0)
res_arch_101 = run_telemetry_match(lambda: arch.ArchBaseAgent(full_flags), v2.agent, 101, seat=0)

with open("scratch/telemetry_arch_base_seed215.json", "w") as f:
    json.dump(res_arch_215["trace"], f, indent=2)

with open("scratch/telemetry_v2_seed215.json", "w") as f:
    json.dump(res_v2_215["trace"], f, indent=2)

with open("scratch/telemetry_arch_base_seed101.json", "w") as f:
    json.dump(res_arch_101["trace"], f, indent=2)

print("\nSaved full 720-step telemetry files.")
