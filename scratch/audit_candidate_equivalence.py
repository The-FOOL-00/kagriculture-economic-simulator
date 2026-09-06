import os
import sys
import importlib.util
from kaggle_environments import make

def load_agent(path):
    spec = importlib.util.spec_from_file_location("agent_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent

def test_pair_equivalence(cand1_name, cand1_path, cand2_name, cand2_path, seeds=[42, 100, 2026, 777, 999]):
    print("=" * 80)
    print(f"TESTING BEHAVIORAL EQUIVALENCE: {cand1_name} vs {cand2_name}")
    print("=" * 80)
    
    agent1 = load_agent(cand1_path)
    agent2 = load_agent(cand2_path)
    
    # Run against a fixed opponent (Aethel V1)
    opp_path = "main.py"
    
    all_identical = True
    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}
        
        # Run Match 1
        env1 = make("kaggriculture", configuration=cfg, debug=False)
        env1.run([cand1_path, opp_path])
        
        # Run Match 2
        env2 = make("kaggriculture", configuration=cfg, debug=False)
        env2.run([cand2_path, opp_path])
        
        r1 = env1.steps[-1][0].reward
        r2 = env2.steps[-1][0].reward
        
        # Check turn by turn action identity
        diff_steps = []
        for step_idx in range(len(env1.steps)):
            act1 = env1.steps[step_idx][0].action
            act2 = env2.steps[step_idx][0].action
            if act1 != act2:
                diff_steps.append((step_idx, act1, act2))
                
        # Inspect state at Day 1 (step 24), Day 5 (step 120), Day 10 (step 240), Day 15 (step 360), final (720)
        def get_state(env, step):
            obs = env.steps[step][0].observation
            farm = obs["farms"][0]
            money = farm["money"]
            hands = len(farm["hands"])
            return money, hands
            
        d1_m1, d1_h1 = get_state(env1, 24)
        d5_m1, d5_h1 = get_state(env1, 120)
        d10_m1, d10_h1 = get_state(env1, 240)
        d15_m1, d15_h1 = get_state(env1, 360)
        
        d1_m2, d1_h2 = get_state(env2, 24)
        d5_m2, d5_h2 = get_state(env2, 120)
        d10_m2, d10_h2 = get_state(env2, 240)
        d15_m2, d15_h2 = get_state(env2, 360)
        
        match = (len(diff_steps) == 0 and r1 == r2)
        if not match:
            all_identical = False
            
        print(f"Seed {s}: Match={match} | R1=${r1:,.1f}, R2=${r2:,.1f} | Diff Steps Count={len(diff_steps)}")
        print(f"  Day 1:  M1=${d1_m1:.1f}, H1={d1_h1} vs M2=${d1_m2:.1f}, H2={d1_h2}")
        print(f"  Day 5:  M1=${d5_m1:.1f}, H1={d5_h1} vs M2=${d5_m2:.1f}, H2={d5_h2}")
        print(f"  Day 10: M1=${d10_m1:.1f}, H1={d10_h1} vs M2=${d10_m2:.1f}, H2={d10_h2}")
        print(f"  Day 15: M1=${d15_m1:.1f}, H1={d15_h1} vs M2=${d15_m2:.1f}, H2={d15_h2}")
        
    print(f"\nVERDICT for {cand1_name} vs {cand2_name}: {'100% BIT-FOR-BIT IDENTICAL (INERT)' if all_identical else 'DIFFERENT'}\n")
    return all_identical

if __name__ == "__main__":
    pairs = [
        ("Candidate A (V2 Base)", "candidates/counterstrategy_ablation/candidate_A.py",
         "Candidate C (Early Ramp)", "candidates/counterstrategy_ablation/candidate_C.py"),
        ("Candidate B (Cap12)", "candidates/counterstrategy_ablation/candidate_B.py",
         "Candidate E (Cap12+Ramp)", "candidates/counterstrategy_ablation/candidate_E.py"),
        ("Candidate D (Preempt)", "candidates/counterstrategy_ablation/candidate_D.py",
         "Candidate G (Ramp+Preempt)", "candidates/counterstrategy_ablation/candidate_G.py"),
        ("Candidate F (Cap12+Preempt)", "candidates/counterstrategy_ablation/candidate_F.py",
         "Candidate H (All3)", "candidates/counterstrategy_ablation/candidate_H.py")
    ]
    
    for c1_n, c1_p, c2_n, c2_p in pairs:
        test_pair_equivalence(c1_n, c1_p, c2_n, c2_p)
