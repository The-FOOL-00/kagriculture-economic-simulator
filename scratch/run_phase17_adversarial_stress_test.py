import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np

def run_adversarial_attack_test():
    print("================================================================================")
    print("PHASE 17: ADVERSARIAL STRESS TEST & ATTACK GAUNTLET")
    print("================================================================================")
    
    attacks = [
        ("Baseline (No Attack)", {"episodeSteps": 720, "seed": 42}),
        ("Starting Cash Reduced to $500", {"episodeSteps": 720, "seed": 42, "startingMoney": 500}),
        ("Starting Cash Increased to $10,000", {"episodeSteps": 720, "seed": 42, "startingMoney": 10000}),
        ("High Weed Probability (5x)", {"episodeSteps": 720, "seed": 42, "weedProbability": 0.05}),
        ("High Farm Hand Cost (2x)", {"episodeSteps": 720, "seed": 42, "hireCostMultiplier": 2.0}),
        ("Fast Town Consumption (2 turns)", {"episodeSteps": 720, "seed": 42, "consumptionInterval": 2}),
        ("Extreme Unseen Seed 999999999", {"episodeSteps": 720, "seed": 999999999}),
        ("Extreme Unseen Seed 123456789", {"episodeSteps": 720, "seed": 123456789}),
        ("Extreme Unseen Seed 888888888", {"episodeSteps": 720, "seed": 888888888}),
    ]
    
    results = {}
    
    for attack_name, config in attacks:
        print(f"\n--- Testing Attack: {attack_name} ---")
        
        # 1. Candidate V2 Adaptive Overlay
        env_ov = kaggle_environments.make("kaggriculture", configuration=config)
        env_ov.run(["candidates/candidate_v2_adaptive_overlay.py", "starter"])
        score_ov = env_ov.steps[-1][0]["reward"]
        
        # 2. Frozen V2 Baseline
        env_v2 = kaggle_environments.make("kaggriculture", configuration=config)
        env_v2.run(["candidates/slot2_aethel_refined_v2.py", "starter"])
        score_v2 = env_v2.steps[-1][0]["reward"]
        
        # 3. Grandmaster (Closed-Loop Baseline)
        env_gm = kaggle_environments.make("kaggriculture", configuration=config)
        env_gm.run(["candidates/candidate_cl_aethel_grandmaster.py", "starter"])
        score_gm = env_gm.steps[-1][0]["reward"]
        
        diff_ov_v2 = score_ov - score_v2
        
        print(f"  Adaptive Overlay : ${score_ov:>10.2f}")
        print(f"  Frozen V2        : ${score_v2:>10.2f}")
        print(f"  CL Grandmaster   : ${score_gm:>10.2f}")
        print(f"  Delta (OV - V2)  : ${diff_ov_v2:>+10.2f}")
        
        results[attack_name] = {
            "overlay_score": score_ov,
            "v2_score": score_v2,
            "gm_score": score_gm,
            "delta_ov_v2": diff_ov_v2
        }
        
    with open('scratch/overlay_adversarial_stress_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    return results

if __name__ == '__main__':
    run_adversarial_attack_test()
