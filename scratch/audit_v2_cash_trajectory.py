"""
Forensic script to trace V2's exact cash trajectory across 50 seeds.
"""

import os
import sys
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as lf
import opponents.replay_crop_dusta as cd
import candidates.slot1_titan_control as v1

def run_trace(seeds=range(10000, 10050), opp_name="live_flooder", opp_agent=lf.agent):
    print(f"=== Running 50 Seeds vs {opp_name} ===")
    results = []
    
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([v2.agent, opp_agent])
        
        # Extract step observations
        checkpoints = [72, 120, 144, 168, 192, 216, 240, 255, 256, 360, 480, 600, 719]
        cp_data = {}
        
        for cp in checkpoints:
            if cp < len(env.steps):
                obs = env.steps[cp][0]["observation"]
                farm = obs["farms"][0]
                cp_data[f"m_{cp}"] = float(farm.get("money", 0))
                cp_data[f"q_{cp}"] = len(farm.get("unlocked_quadrants", []))
                cp_data[f"h_{cp}"] = len(farm.get("hands", []))
                
        final_r_us = float(env.steps[-1][0]["reward"] or 0)
        final_r_opp = float(env.steps[-1][1]["reward"] or 0)
        
        results.append({
            "seed": seed,
            "final_us": final_r_us,
            "final_opp": final_r_opp,
            "margin": final_r_us - final_r_opp,
            "m_216": cp_data.get("m_216", 0),
            "q_216": cp_data.get("q_216", 0),
            "m_255": cp_data.get("m_255", 0),
            "q_255": cp_data.get("q_255", 0),
            "q_256": cp_data.get("q_256", 0),
            "m_120": cp_data.get("m_120", 0),
            "m_240": cp_data.get("m_240", 0),
            "m_360": cp_data.get("m_360", 0),
        })
        
    m216_vals = [r["m_216"] for r in results]
    afford_216 = sum(1 for m in m216_vals if m >= 4000)
    
    print(f"Total Seeds: {len(results)}")
    print(f"Money at T216 (Day 9, Hour 0): Mean=${np.mean(m216_vals):.1f} +/- ${np.std(m216_vals):.1f}, Min=${np.min(m216_vals):.1f}, Max=${np.max(m216_vals):.1f}")
    print(f"Seeds with Money >= $4,000 at T216: {afford_216}/{len(results)} ({afford_216/len(results)*100:.1f}%)")
    
    m255_vals = [r["m_255"] for r in results]
    afford_255 = sum(1 for m in m255_vals if m >= 4000)
    print(f"Money at T255 (Day 10, Hour 15): Mean=${np.mean(m255_vals):.1f} +/- ${np.std(m255_vals):.1f}, Min=${np.min(m255_vals):.1f}, Max=${np.max(m255_vals):.1f}")
    print(f"Seeds with Money >= $4,000 at T255: {afford_255}/{len(results)} ({afford_255/len(results)*100:.1f}%)")
    
    q256_vals = [r["q_256"] for r in results]
    print(f"Quadrants unlocked at T256: 3 Quadrants in {sum(1 for q in q256_vals if q >= 3)}/{len(results)} seeds")
    print(f"Mean Final Cash: Us=${np.mean([r['final_us'] for r in results]):.1f}, Opp=${np.mean([r['final_opp'] for r in results]):.1f}, Net=${np.mean([r['margin'] for r in results]):.1f}")
    
    return results

if __name__ == "__main__":
    run_trace(range(10000, 10050), "live_flooder_v1", lf.agent)
    run_trace(range(10000, 10050), "replay_crop_dusta", cd.agent)
    run_trace(range(10000, 10050), "slot1_titan_v1", v1.agent)
