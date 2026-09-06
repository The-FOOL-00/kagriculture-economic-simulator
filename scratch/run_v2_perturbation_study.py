"""
scratch/run_v2_perturbation_study.py
Controlled Perturbation Experiment: Compares Raw V2 vs Guarded V2 under
external environment and execution perturbations across 50 matched seeds.
"""

import sys
sys.path.insert(0, ".")
import math
import json
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.v2_safety_overlay as overlay

SEEDS = [20000 + i * 41 for i in range(50)]

def run_match(seed, agent_type, perturbation_type):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    agent = overlay.V2SafetyOverlayAgent() if agent_type == "guarded" else v2.agent
    
    for step in range(719):
        obs0 = env.state[0].observation
        act0 = agent(obs0)
        
        # Apply controlled perturbation to Player 0
        if perturbation_type == "p1_missed_melon_water" and step == 3 * 24 + 12:
            # Drop watering action at Hour 12 of Day 3
            if act0.get("farmer") == ["WATER"]:
                act0["farmer"] = ["PASS"]
            for h in act0.get("hands", []):
                if h == ["WATER"]:
                    h[0] = "PASS"
                    
        elif perturbation_type == "p2_delayed_build" and step == 4:
            # Cancel pasture build at Step 4
            for h in act0.get("hands", []):
                if h == ["BUILD_PASTURE"]:
                    h[0] = "PASS"
                    
        env.step([act0, v2.agent])
        
    reward = float(env.steps[-1][0]["reward"])
    interventions = getattr(agent, "guard_interventions", 0) if agent_type == "guarded" else 0
    return reward, interventions


def main():
    print("=" * 85)
    print("V2 PERTURBATION ROBUSTNESS BENCHMARK (N=50 MATCHED SEEDS)")
    print("=" * 85)
    
    perturbations = [
        ("None (Unperturbed Baseline)", "none"),
        ("P1: Dropped Day-3 Melon Water Action", "p1_missed_melon_water"),
        ("P2: Canceled Step-4 Pasture Build Action", "p2_delayed_build"),
    ]
    
    summary_results = {}
    
    for p_name, p_code in perturbations:
        print(f"\nEvaluating Perturbation: {p_name}...")
        
        v2_scores = []
        guarded_scores = []
        total_interventions = 0
        
        for s in SEEDS:
            # 1. Raw V2 under perturbation
            r_v2, _ = run_match(s, "raw_v2", p_code)
            v2_scores.append(r_v2)
            
            # 2. Guarded V2 under perturbation
            r_g, inter = run_match(s, "guarded", p_code)
            guarded_scores.append(r_g)
            total_interventions += inter
            
        m_v2 = sum(v2_scores) / len(v2_scores)
        m_g = sum(guarded_scores) / len(guarded_scores)
        delta = m_g - m_v2
        pct = (delta / m_v2) * 100.0 if m_v2 > 0 else 0.0
        
        print(f"  Raw V2 Mean Score:     ${m_v2:,.1f}")
        print(f"  Guarded V2 Mean Score: ${m_g:,.1f}")
        print(f"  Net Robustness Margin: ${delta:+,.1f} ({pct:+.2f}%)")
        print(f"  Total Interventions:   {total_interventions}")
        
        summary_results[p_code] = {
            "name": p_name,
            "raw_v2_mean": m_v2,
            "guarded_mean": m_g,
            "delta": delta,
            "pct": pct,
            "interventions": total_interventions
        }
        
    with open("scratch/perturbation_study_summary.json", "w") as f:
        json.dump(summary_results, f, indent=2)
        
    print("\nPerturbation study complete. Saved to scratch/perturbation_study_summary.json.")


if __name__ == "__main__":
    main()
