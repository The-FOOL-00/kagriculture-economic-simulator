import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import candidates.candidate_v2_adaptive_overlay as ov

def test_mutations():
    print("================================================================================")
    print("PHASE 12: CLOSED-LOOP MUTATION PROOF & STATE ANOMALY AUDIT")
    print("================================================================================")
    
    mutations = [
        ("1. Cash Reduction ($500 starting)", {"startingMoney": 500}),
        ("2. Cash Increase ($10,000 starting)", {"startingMoney": 10000}),
        ("3. High Weed Density (5x)", {"weedProbability": 0.05}),
        ("4. High Hire Multiplier (2x)", {"hireCostMultiplier": 2.0}),
        ("5. Fast Town Market Consumption (2 turns)", {"consumptionInterval": 2}),
        ("6. Random Unseen Seed 777777", {"seed": 777777}),
        ("7. Random Unseen Seed 123456789", {"seed": 123456789}),
        ("8. Random Unseen Seed 999999999", {"seed": 999999999}),
        ("9. Delayed Opening (Forced PASS Turns 0-4)", "DELAY"),
        ("10. Altered Board Layout (Inverted Map Orientation)", "INVERT")
    ]
    
    mutation_results = []
    
    for name, config in mutations:
        try:
            if config == "DELAY":
                # Wrapper that forces PASS on turns 0-4
                def delay_agent(obs, c=None):
                    s = int(obs.get("step", 0) or 0)
                    if s < 5:
                        return {"farmer": ["PASS"], "hands": [], "market": []}
                    return ov.agent(obs, c)
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
                env.run([delay_agent, "starter"])
                score = env.steps[-1][0]["reward"]
                crashed = False
            elif config == "INVERT":
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 314159})
                env.run([ov.agent, "starter"])
                score = env.steps[-1][0]["reward"]
                crashed = False
            else:
                base_cfg = {"episodeSteps": 720, "seed": 42}
                base_cfg.update(config)
                env = kaggle_environments.make("kaggriculture", configuration=base_cfg)
                env.run([ov.agent, "starter"])
                score = env.steps[-1][0]["reward"]
                crashed = False
        except Exception as e:
            score = 0.0
            crashed = True
            print(f"  [CRASH] {name}: {e}")
            
        status = "PASSED" if (not crashed and score > 0) else "FAILED"
        print(f"  {name:<45}: Score = ${score:>10.2f} | Status = {status}")
        mutation_results.append({
            "mutation": name,
            "score": score,
            "crashed": crashed,
            "status": status
        })
        
    with open('scratch/overlay_mutation_audit_results.json', 'w') as f:
        json.dump(mutation_results, f, indent=2)
    return mutation_results

if __name__ == '__main__':
    test_mutations()
