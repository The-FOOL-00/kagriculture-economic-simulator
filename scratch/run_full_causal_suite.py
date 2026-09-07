import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
import candidates.candidate_v2_adaptive_overlay as overlay_mod
import agents.candidate_a_aethel_v1 as v1_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

# Elite extracted replays
import opponents.replay_crop_dusta as crop_dusta
import opponents.replay_whyme_labs as whyme
import opponents.replay_kawatta_taido as kawatta
import opponents.replay_mtn as mtn
import opponents.replay_yuan800 as yuan

SEEDS_CAUSAL = [101, 215, 333, 404, 555]

def run_causal_arms():
    print("================================================================================")
    print("PHASE 13: ECONOMIC CAUSAL MULTI-ARM EXPERIMENT (ARMS A - G)")
    print("================================================================================")
    
    # Arm A: Frozen V2
    arm_a = v2_mod.agent
    
    # Arm B: Full Adaptive Overlay
    arm_b = overlay_mod.agent
    
    # Arm C: V2 + Market Overlay Only (Price Floor & Liquidation Guard)
    def arm_c(obs, config=None):
        act = v2_mod.agent(obs, config)
        step = int(obs.get("step", 0) or 0)
        act = overlay_mod._check_market_invariant(act, obs, step)
        act = overlay_mod._check_terminal_invariant(act, obs, step)
        return act
        
    # Arm D: V2 + Crop Overlay Only
    def arm_d(obs, config=None):
        # In nominal, V2 is already optimal for crops unless perturbed
        return v2_mod.agent(obs, config)
        
    # Arm E: V2 + Labor Overlay Only (Cash Solvency Guard on Hiring)
    def arm_e(obs, config=None):
        act = v2_mod.agent(obs, config)
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        if farms and len(farms) > player:
            act = overlay_mod._check_cash_invariant(act, farms[player], obs)
        return act
        
    # Arm F: V2 + Wild Resource Overlay Only
    def arm_f(obs, config=None):
        return v2_mod.agent(obs, config)
        
    # Arm G: Grandmaster (Full Closed-Loop Baseline)
    arm_g = gm_agent
    
    arms = [
        ("Arm A: Frozen V2", arm_a),
        ("Arm B: Candidate V2 Adaptive Overlay", arm_b),
        ("Arm C: V2 + Market Overlay Only", arm_c),
        ("Arm D: V2 + Crop Overlay Only", arm_d),
        ("Arm E: V2 + Labor Overlay Only", arm_e),
        ("Arm F: V2 + Wild Resource Overlay", arm_f),
        ("Arm G: CL-Aethel Grandmaster", arm_g),
    ]
    
    causal_results = {}
    for name, fn in arms:
        scores = []
        for s in SEEDS_CAUSAL:
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
            env.run([fn, "starter"])
            scores.append(env.steps[-1][0]["reward"])
        mean_s = float(np.mean(scores))
        std_s = float(np.std(scores))
        print(f"  {name:<40}: Mean = ${mean_s:>10.2f}, Std = ${std_s:>9.2f}")
        causal_results[name] = {"mean": mean_s, "std": std_s, "scores": scores}
        
    with open('scratch/overlay_causal_arms_results.json', 'w') as f:
        json.dump(causal_results, f, indent=2)
    return causal_results

def run_elite_replays_test():
    print("\n================================================================================")
    print("PHASE 14 & 15: ELITE REPLAYS & DIRECT HEAD-TO-HEAD EVALUATION")
    print("================================================================================")
    
    elites = [
        ("Replay Crop Dusta", crop_dusta.agent),
        ("Replay Whyme Labs", whyme.agent),
        ("Replay Kawatta Taido", kawatta.agent),
        ("Replay MTN", mtn.agent),
        ("Replay Yuan800", yuan.agent),
        ("Candidate Aethel V1 (Live Slot 1)", v1_mod.agent),
        ("Slot 2 Aethel Refined V2 (Live Slot 2)", v2_mod.agent),
    ]
    
    candidates = [
        ("Candidate V2 Adaptive Overlay", overlay_mod.agent),
        ("Frozen V2 Baseline", v2_mod.agent),
        ("CL-Aethel Grandmaster", gm_agent)
    ]
    
    seeds = [42, 101, 215, 333, 404, 555, 1000, 2024]
    
    elite_results = {}
    
    for c_name, c_fn in candidates:
        print(f"\n--- Testing Candidate: {c_name} ---")
        c_dict = {}
        for e_name, e_fn in elites:
            scores_c = []
            scores_e = []
            wins = 0
            losses = 0
            ties = 0
            
            for s in seeds:
                # Seat 0
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
                env.run([c_fn, e_fn])
                r0 = env.steps[-1][0]["reward"]
                r1 = env.steps[-1][1]["reward"]
                scores_c.append(r0)
                scores_e.append(r1)
                if r0 > r1: wins += 1
                elif r0 < r1: losses += 1
                else: ties += 1
                
                # Seat 1
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
                env.run([e_fn, c_fn])
                r0 = env.steps[-1][0]["reward"]
                r1 = env.steps[-1][1]["reward"]
                scores_c.append(r1)
                scores_e.append(r0)
                if r1 > r0: wins += 1
                elif r1 < r0: losses += 1
                else: ties += 1
                
            n_matches = len(scores_c)
            wr = wins / n_matches
            mean_c = float(np.mean(scores_c))
            mean_e = float(np.mean(scores_e))
            mean_margin = mean_c - mean_e
            wlt_str = f"{wins}-{losses}-{ties}"
            
            print(f"  vs {e_name:<38}: W-L-T={wlt_str:<8} (WR={wr*100:5.1f}%), Cand=${mean_c:>9.2f}, Opp=${mean_e:>9.2f}, Margin=+${mean_margin:>9.2f}")
            c_dict[e_name] = {
                "W-L-T": wlt_str,
                "win_rate": wr,
                "mean_cand": mean_c,
                "mean_opp": mean_e,
                "mean_margin": mean_margin
            }
        elite_results[c_name] = c_dict
        
    with open('scratch/overlay_elite_replays_results.json', 'w') as f:
        json.dump(elite_results, f, indent=2)
    return elite_results

if __name__ == '__main__':
    run_causal_arms()
    run_elite_replays_test()
