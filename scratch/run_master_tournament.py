"""
Phase 11 & 12: Master Tournament & Statistical Evaluation Suite.
Evaluates Candidate CL-Aethel Prime against:
1. Frozen V2 (Slot 2 Live Anchor)
2. Frozen V1 (Slot 1 Live Anchor)
3. Golden V1 (Apex Grandmaster)
4. Synthetic Suite (Melon Burst, Strawberry Rush, Crop Efficient)
5. Pass Baseline

Splits:
- Development Split: Seeds 101 to 120 (20 matched seeds)
- Holdout Split: Seeds 501 to 520 (20 matched seeds)
"""

import sys, os, time
import numpy as np
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from agents.candidate_a_aethel_v1 import agent as v1_agent
from agents.expanded_opponent_suite import (
    golden_v1_agent, melon_burst_agent, strawberry_rush_agent, crop_efficient_agent
)

pass_ag = lambda obs, cfg=None: {}

DEV_SEEDS = list(range(101, 121))     # 20 seeds
HOLDOUT_SEEDS = list(range(501, 521)) # 20 seeds

OPPONENT_MAP = {
    "Frozen V2 (Slot 2)": v2_agent,
    "Frozen V1 (Slot 1)": v1_agent,
    "Golden V1 (Grandmaster)": golden_v1_agent,
    "Melon Burst": melon_burst_agent,
    "Strawberry Rush": strawberry_rush_agent,
    "Crop Efficient": crop_efficient_agent,
    "Pass Agent": pass_ag,
}

def evaluate_suite(candidate, opponents, seeds, split_name="Dev"):
    print(f"\n{'='*80}\nRUNNING TOURNAMENT: {split_name.upper()} SPLIT ({len(seeds)} SEEDS)\n{'='*80}")
    summary = {}
    
    for opp_name, opp_ag in opponents.items():
        margins = []
        c_scores = []
        o_scores = []
        wins, losses, ties = 0, 0, 0
        
        t0 = time.time()
        for s in seeds:
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
            env.run([candidate, opp_ag])
            r_c = env.state[0].reward
            r_o = env.state[1].reward
            m = r_c - r_o
            margins.append(m)
            c_scores.append(r_c)
            o_scores.append(r_o)
            if m > 0: wins += 1
            elif m < 0: losses += 1
            else: ties += 1
            
        dur = time.time() - t0
        mean_m = np.mean(margins)
        median_m = np.median(margins)
        std_m = np.std(margins)
        win_rate = (wins / len(seeds)) * 100.0
        
        summary[opp_name] = {
            "mean_cand": np.mean(c_scores),
            "mean_opp": np.mean(o_scores),
            "mean_margin": mean_m,
            "median_margin": median_m,
            "std_margin": std_m,
            "wins": wins, "losses": losses, "ties": ties,
            "win_rate": win_rate,
            "ci_95": 1.96 * (std_m / np.sqrt(len(seeds)))
        }
        
        print(f"  vs {opp_name:24s} | WinRate: {win_rate:5.1f}% ({wins}W-{losses}L-{ties}T) | Mean Margin: ${mean_m:+10,.1f} +/- ${summary[opp_name]['ci_95']:,.1f} | Cand: ${np.mean(c_scores):,.1f} vs Opp: ${np.mean(o_scores):,.1f} ({dur:.1f}s)")
        
    return summary

if __name__ == "__main__":
    dev_results = evaluate_suite(prime_agent, OPPONENT_MAP, DEV_SEEDS, "Development")
    holdout_results = evaluate_suite(prime_agent, OPPONENT_MAP, HOLDOUT_SEEDS, "Holdout")
