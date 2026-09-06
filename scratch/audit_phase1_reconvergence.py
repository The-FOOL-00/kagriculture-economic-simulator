"""
Phase 1: Prove Exactly What Part of H is Unique & Find Reconvergence Point
Compares V2 vs H replay-derived trace step by step from Step 0 through Step 719.
Tracks actions and game states to find the earliest point where trajectories can converge.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

def run_audit():
    seed = 42
    cfg = {"seed": seed, "episodeSteps": 720}
    
    env_v2 = make("kaggriculture", configuration=cfg)
    env_v2.run([robust(v2.agent), robust(v2.agent)])
    
    env_h = make("kaggriculture", configuration=cfg)
    env_h.run([robust(agent_H_full_jit_pipeline), robust(v2.agent)])
    
    print(f"Comparing V2 vs H across 720 steps on Seed {seed}...")
    
    comparison_log = []
    
    # Key check milestones
    milestone_steps = [0, 1, 2, 5, 10, 18, 23, 24, 25, 48, 72, 96, 120, 150, 200, 240, 264, 265, 266, 288, 336, 500, 712, 719]
    
    for s in range(720):
        step_v2 = env_v2.steps[s]
        step_h = env_h.steps[s]
        
        obs_v2 = step_v2[0]["observation"]
        obs_h = step_h[0]["observation"]
        
        farm_v2 = obs_v2["farms"][0]
        farm_h = obs_h["farms"][0]
        
        act_v2 = step_v2[0].get("action", {})
        act_h = step_h[0].get("action", {})
        
        # Extract counts
        def get_crop_counts(tiles):
            counts = {}
            for r in tiles:
                for t in r:
                    if isinstance(t, dict):
                        k = t.get("crop") or t.get("structure") or t.get("kind")
                        if k:
                            counts[k] = counts.get(k, 0) + 1
            return counts

        crops_v2 = get_crop_counts(farm_v2["tiles"])
        crops_h = get_crop_counts(farm_h["tiles"])
        
        rec = {
            "step": s,
            "day": s // 24,
            "hour": s % 24,
            "v2_money": farm_v2.get("money", 0),
            "h_money": farm_h.get("money", 0),
            "v2_hands": len(farm_v2.get("hands", [])),
            "h_hands": len(farm_h.get("hands", [])),
            "v2_crops": crops_v2,
            "h_crops": crops_h,
            "v2_act": act_v2,
            "h_act": act_h,
            "act_equal": (act_v2 == act_h)
        }
        comparison_log.append(rec)
        
        if s in milestone_steps:
            print(f"Step {s:3d} (Day {s//24:2d}, Hr {s%24:2d}):")
            print(f"  V2: Money=${farm_v2.get('money',0):7.1f} | Hands={len(farm_v2.get('hands',[]))} | Crops={crops_v2}")
            print(f"  H : Money=${farm_h.get('money',0):7.1f} | Hands={len(farm_h.get('hands',[]))} | Crops={crops_h}")
            print(f"  V2 Act: Farmer={act_v2.get('farmer')} | Mkt={act_v2.get('market')}")
            print(f"  H  Act: Farmer={act_h.get('farmer')} | Mkt={act_h.get('market')}")
            print(f"  Actions Equal: {act_v2 == act_h}\n")
            
    with open("scratch/jit_melon_results/phase1_reconvergence_audit.json", "w") as f:
        # Save summary of milestones
        milestone_data = [comparison_log[s] for s in milestone_steps]
        json.dump(milestone_data, f, indent=2)
        
    print("Saved Phase 1 reconvergence audit to scratch/jit_melon_results/phase1_reconvergence_audit.json")

if __name__ == "__main__":
    run_audit()
