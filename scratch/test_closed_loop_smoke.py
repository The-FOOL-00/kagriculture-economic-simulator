import sys
import os
sys.path.insert(0, ".")
import json
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

smoke_seeds = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
               201, 202, 203, 204, 205, 206, 207, 208, 209, 215620170]

print("="*95)
print(f"{'Seed':<10} | {'Candidate':<12} | {'V2 Baseline':<12} | {'Margin':<12} | {'Pastures':<9} | {'Cows':<6} | {'Sheep':<6} | {'Quads':<12}")
print("="*95)

scores_cand = []
scores_v2 = []
margins = []

for s in smoke_seeds:
    env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
    env.run([cl_arch.agent, v2.agent])
    
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    
    obs0 = env.steps[-1][0]["observation"]
    farm0 = obs0["farms"][0]
    tiles0 = farm0["tiles"]
    
    past0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    cows0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    sheep0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
    quads0 = ",".join(farm0.get("unlocked_quadrants", []))
    
    scores_cand.append(r0)
    scores_v2.append(r1)
    margin = r0 - r1
    margins.append(margin)
    
    print(f"{s:<10d} | ${r0:<11,.0f} | ${r1:<11,.0f} | ${margin:<11,.0f} | {past0:<2d}/16    | {cows0:<6d} | {sheep0:<6d} | {quads0:<12}")

import numpy as np
print("="*95)
print(f"SMOKE TEST SUMMARY (N={len(smoke_seeds)}):")
print(f"  Candidate Mean: ${np.mean(scores_cand):,.1f} +/- ${np.std(scores_cand):,.1f}")
print(f"  V2 Baseline:   ${np.mean(scores_v2):,.1f} +/- ${np.std(scores_v2):,.1f}")
print(f"  Mean Margin:   ${np.mean(margins):+,.1f}")
print(f"  Win Rate:      {sum(1 for m in margins if m > 0) / len(margins) * 100:.1f}% ({sum(1 for m in margins if m > 0)}/{len(margins)})")
print("="*95)
