"""
scratch/test_noninterference.py
Verifies that V2SafetyOverlay produces ZERO behavioral changes on standard unperturbed games.
"""

import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.v2_safety_overlay as overlay

SEEDS = [10000 + i * 37 for i in range(50)]

def test_seed(seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    over_agent = overlay.V2SafetyOverlayAgent()
    
    mismatches = 0
    total_steps = 719
    
    for step in range(total_steps):
        obs0 = env.state[0].observation
        
        # Get raw V2 action
        raw_v2_act = v2.agent(obs0)
        # Get overlay action
        over_act = over_agent(obs0)
        
        # Check equality
        f_eq = (raw_v2_act.get("farmer") == over_act.get("farmer"))
        h_eq = (raw_v2_act.get("hands") == over_act.get("hands"))
        m_eq = (raw_v2_act.get("market") == over_act.get("market"))
        
        if not (f_eq and h_eq and m_eq):
            mismatches += 1
            
        env.step([raw_v2_act, v2.agent])
        
    return mismatches, over_agent.guard_interventions


def main():
    print("================================================================================")
    print("VERIFYING SAFETY OVERLAY NON-INTERFERENCE PROPERTY (N=50 NORMAL SEEDS)")
    print("================================================================================")
    
    total_mismatches = 0
    total_interventions = 0
    
    for s_idx, s in enumerate(SEEDS):
        m, inter = test_seed(s)
        total_mismatches += m
        total_interventions += inter
        if m > 0 or inter > 0:
            print(f"Seed {s}: Mismatches={m}, Interventions={inter}")
            
    print(f"\nRESULTS ACROSS {len(SEEDS)} SEEDS (35,950 STEPS TOTAL):")
    print(f"  Total Action Mismatches:    {total_mismatches}")
    print(f"  Total Guard Interventions:  {total_interventions}")
    print(f"  Action Equality vs V2:      {(35950 - total_mismatches)/35950 * 100:.4f}%")
    
    if total_mismatches == 0 and total_interventions == 0:
        print("\n>>> NON-INTERFERENCE VERIFIED: 100% BIT-IDENTICAL BEHAVIOR ON NORMAL GAMES <<<")
    else:
        print("\n>>> WARNING: NON-INTERFERENCE VIOLATED <<<")


if __name__ == "__main__":
    main()
