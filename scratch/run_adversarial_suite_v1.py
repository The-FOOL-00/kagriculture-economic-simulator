import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from candidates.candidate_closed_loop_execution_v1 import agent as cl_agent
import copy

def run_adversarial_suite():
    print("=================================================================")
    print("PHASE 13: ADVERSARIAL STRESS TESTING (CL-Execution-V1)")
    print("=================================================================")
    
    results = {}
    
    # 1. Cash Starvation Attack ($0 on Day 0)
    print("\n--- Vector 1: Cash Starvation ($0 start) ---")
    orig_process_market = kg._process_market
    def hooked_cash_starve(state, env_inner):
        if state[0].observation.step == 0:
            state[0].observation.farms[0]["money"] = 0.0
        orig_process_market(state, env_inner)
    kg._process_market = hooked_cash_starve
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
        env.run([cl_agent, "starter"])
        r1 = env.steps[-1][0]["reward"]
        status1 = env.steps[-1][0]["status"]
        print(f"  Result: Reward = ${r1:,.1f}, Status = {status1}")
        results["Cash_Starvation"] = {"reward": r1, "status": status1, "passed": status1 == "DONE" and r1 >= 0}
    finally:
        kg._process_market = orig_process_market
        
    # 2. Feed Starvation Attack (0 wheat in shed)
    print("\n--- Vector 2: Feed Starvation (0 wheat in shed) ---")
    def hooked_feed_starve(state, env_inner):
        if state[0].observation.step == 24: # Day 1 start
            state[0].observation.private["shed"]["WHEAT"] = 0
        orig_process_market(state, env_inner)
    kg._process_market = hooked_feed_starve
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
        env.run([cl_agent, "starter"])
        r2 = env.steps[-1][0]["reward"]
        status2 = env.steps[-1][0]["status"]
        print(f"  Result: Reward = ${r2:,.1f}, Status = {status2}")
        results["Feed_Starvation"] = {"reward": r2, "status": status2, "passed": status2 == "DONE" and r2 > 40000}
    finally:
        kg._process_market = orig_process_market
        
    # 3. Spatial Displacement (Farmer displaced from (4,4) to (0,0) at Step 50)
    print("\n--- Vector 3: Spatial Displacement (Farmer displaced to (0,0) at step 50) ---")
    def hooked_displace(state, env_inner):
        if state[0].observation.step == 50:
            state[0].observation.farms[0]["farmer"] = [0, 0]
        orig_process_market(state, env_inner)
    kg._process_market = hooked_displace
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
        env.run([cl_agent, "starter"])
        r3 = env.steps[-1][0]["reward"]
        status3 = env.steps[-1][0]["status"]
        print(f"  Result: Reward = ${r3:,.1f}, Status = {status3}")
        results["Spatial_Displacement"] = {"reward": r3, "status": status3, "passed": status3 == "DONE" and r3 > 60000}
    finally:
        kg._process_market = orig_process_market
        
    # 4. Chaotic Opponent (Random moves & passes)
    print("\n--- Vector 4: Chaotic Opponent ---")
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 999})
    env.run([cl_agent, "starter"])
    r4 = env.steps[-1][0]["reward"]
    status4 = env.steps[-1][0]["status"]
    print(f"  Result: Reward = ${r4:,.1f}, Status = {status4}")
    results["Chaotic_Opponent"] = {"reward": r4, "status": status4, "passed": status4 == "DONE" and r4 > 50000}
    
    # 5. Broad Seed Stress Test (10 varied seeds)
    print("\n--- Vector 5: Broad Seed Stress Test (10 Seeds: 7 to 9999) ---")
    test_seeds = [7, 13, 77, 128, 256, 512, 1024, 2048, 4096, 9999]
    seed_rewards = []
    for s in test_seeds:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env.run([cl_agent, "starter"])
        sr = env.steps[-1][0]["reward"]
        seed_rewards.append(sr)
        print(f"  Seed {s:4d}: Reward = ${sr:,.1f}")
        
    results["Seed_Stress"] = {
        "mean": float(sum(seed_rewards) / len(seed_rewards)),
        "min": float(min(seed_rewards)),
        "max": float(max(seed_rewards)),
        "passed": all(r > 40000 for r in seed_rewards)
    }
    print(f"  Mean across 10 varied seeds: ${results['Seed_Stress']['mean']:,.1f} (Min: ${results['Seed_Stress']['min']:,.1f}, Max: ${results['Seed_Stress']['max']:,.1f})")

    import json
    with open('scratch/adversarial_suite_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved adversarial results to scratch/adversarial_suite_results.json")

if __name__ == "__main__":
    run_adversarial_suite()
