import sys, os
sys.path.insert(0, os.path.abspath('.'))
import copy
import json
import kaggle_environments
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

def run_attack_gauntlet():
    print("="*90)
    print("PHASE 13: ADVERSARIAL FALSIFICATION & ATTACK GAUNTLET")
    print("="*90)
    
    attacks = [
        ("Baseline (No Attack)", {}),
        ("Starting Cash Reduced to $500", {"startingMoney": 500}),
        ("Starting Cash Increased to $10,000", {"startingMoney": 10000}),
        ("High Weed Probability (5x)", {"weedSpawnChance": 0.025}),
        ("High Farm Hand Cost (2x Fib)", {"farmHandCostMult": 2}),
        ("Fast Town Consumption (2 turns)", {"townShopSellInterval": 2}),
        ("Extreme Unseen Seed 999999999", {"seed": 999999999}),
        ("Extreme Unseen Seed 123456789", {"seed": 123456789}),
        ("Extreme Unseen Seed 888888888", {"seed": 888888888}),
    ]
    
    results = {}
    
    for attack_name, cfg_override in attacks:
        print(f"\n--- Attack: {attack_name} ---")
        gm_scores = []
        v2_scores = []
        
        test_seeds = [42, 100, 2024] if "seed" not in cfg_override else [cfg_override["seed"]]
        
        for s in test_seeds:
            cfg = {"episodeSteps": 720, "seed": s}
            cfg.update(cfg_override)
            
            # 1. Run Grandmaster
            env = kaggle_environments.make("kaggriculture", configuration=cfg)
            starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
            env.run([gm_agent, starter])
            r_gm = env.steps[-1][0]["reward"]
            gm_scores.append(r_gm)
            
            # 2. Run V2
            env = kaggle_environments.make("kaggriculture", configuration=cfg)
            starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
            env.run([v2_mod.agent, starter])
            r_v2 = env.steps[-1][0]["reward"]
            v2_scores.append(r_v2)
            
        m_gm = float(np.mean(gm_scores))
        m_v2 = float(np.mean(v2_scores))
        print(f"  Grandmaster (Closed-Loop) : ${m_gm:>9,.1f}")
        print(f"  Frozen V2   (Open-Loop)   : ${m_v2:>9,.1f}")
        print(f"  Difference (GM - V2)      : ${m_gm - m_v2:>+9,.1f}")
        
        results[attack_name] = {
            "gm_mean": m_gm,
            "v2_mean": m_v2,
            "diff": m_gm - m_v2,
            "gm_scores": gm_scores,
            "v2_scores": v2_scores
        }

    # Delayed Actions Test: First 5 turns PASS
    print("\n--- Attack: 5-Turn Initial Delay (Forced PASS on turns 0-4) ---")
    def delayed_wrapper(base_agent):
        def wrapper(obs, cfg=None):
            step = int(obs.get("step", 0) or 0)
            if step < 5:
                return {"farmer": ["PASS"], "hands": [], "market": []}
            return base_agent(obs, cfg)
        return wrapper
        
    gm_del_scores = []
    v2_del_scores = []
    for s in [42, 100, 2024]:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([delayed_wrapper(gm_agent), starter])
        gm_del_scores.append(env.steps[-1][0]["reward"])
        
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([delayed_wrapper(v2_mod.agent), starter])
        v2_del_scores.append(env.steps[-1][0]["reward"])
        
    m_gm_del = float(np.mean(gm_del_scores))
    m_v2_del = float(np.mean(v2_del_scores))
    print(f"  Grandmaster (Delayed) : ${m_gm_del:>9,.1f}")
    print(f"  Frozen V2   (Delayed) : ${m_v2_del:>9,.1f}")
    print(f"  Difference (GM - V2)  : ${m_gm_del - m_v2_del:>+9,.1f}")
    results["5-Turn Initial Delay"] = {
        "gm_mean": m_gm_del,
        "v2_mean": m_v2_del,
        "diff": m_gm_del - m_v2_del
    }

    with open("scratch/adversarial_attack_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved attack gauntlet results to scratch/adversarial_attack_results.json")

if __name__ == '__main__':
    run_attack_gauntlet()
