import copy
import json
import os
import sys
import numpy as np

sys.path.insert(0, '.')
from kaggle_environments import make

import candidates.slot2_aethel_refined_v2 as v2_mod
import opponents.replay_crop_dusta as cd_opp
import opponents.replay_whyme_labs as whyme_opp
import opponents.replay_kawatta_taido as kawatta_opp
import opponents.live_flooder_v1 as flooder_opp

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect the seeds to run
test_seeds = [
    215620170, # Seed from 104824599
    104816794, 104817623, 104818466, 104819367,
    104820229, 104821339, 104822515, 104823350, 104824200
]

opponents = [
    ('Whyme_Labs', whyme_opp.agent),
    ('Crop_Dusta', cd_opp.agent),
    ('Kawatta_Taido', kawatta_opp.agent),
    ('Live_Flooder', flooder_opp.agent),
]

# Build the treatments:
# Treatment A: V2 Baseline
def make_v2_baseline():
    return v2_mod.agent

# Treatment B: V2 + same livestock count (8 cows, 6 sheep), strictly zero external wheat
# (In V2 baseline, V2 buys 17 wheat on turn 1 and 258 wheat over the game. Let's see if we suppress non-essential wheat buys)
# Treatment C: V2 + extra purchased wheat (feed buffer buying up to 30), same livestock count
# Treatment D: Extra pasture infrastructure (16 pastures), same livestock (8C/6S)
# Treatment E: Extra pasture (16 pastures) + livestock (12-13 cows, 3 sheep)
# Treatment F: Extra pasture (16) + livestock (13C) + external wheat
# Treatment G: Full reconstructed Crop-Dusta macro sequence (from replay_crop_dusta)

# We can run these across test_seeds against the opponent suite!

print(f"Running Causal Factorial Study across {len(test_seeds)} seeds against {len(opponents)} opponents...")

results = {}

# Let's evaluate:
# 1. Baseline V2
# 2. Replay Crop Dusta (Player 1 macro)
# 3. Treatment C (V2 + extra wheat)
# 4. Treatment G (Crop Dusta Closed-Loop / Replay)

# Let's run a benchmark comparing:
# 1. V2 Baseline
# 2. Crop Dusta Macro
# 3. Whyme Labs Macro
# across the seeds to measure their score distributions and margins.

match_records = []

for seed in test_seeds:
    for opp_name, opp_agent in opponents:
        # Match 1: V2 (Player 0) vs Opponent (Player 1)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([v2_mod.agent, opp_agent])
        r0, r1 = env.steps[-1][0]['reward'], env.steps[-1][1]['reward']
        match_records.append({
            'candidate': 'A_V2_BASELINE',
            'seat': 0,
            'opp': opp_name,
            'seed': seed,
            'cand_score': r0,
            'opp_score': r1,
            'margin': r0 - r1
        })
        
        # Match 2: V2 (Player 1) vs Opponent (Player 0)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([opp_agent, v2_mod.agent])
        r0, r1 = env.steps[-1][0]['reward'], env.steps[-1][1]['reward']
        match_records.append({
            'candidate': 'A_V2_BASELINE',
            'seat': 1,
            'opp': opp_name,
            'seed': seed,
            'cand_score': r1,
            'opp_score': r0,
            'margin': r1 - r0
        })

        # Match 3: Crop Dusta Replay Agent (Player 0) vs Opponent (Player 1)
        if opp_name != 'Crop_Dusta':
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run([cd_opp.agent, opp_agent])
            r0, r1 = env.steps[-1][0]['reward'], env.steps[-1][1]['reward']
            match_records.append({
                'candidate': 'G_CROP_DUSTA_MACRO',
                'seat': 0,
                'opp': opp_name,
                'seed': seed,
                'cand_score': r0,
                'opp_score': r1,
                'margin': r0 - r1
            })

            # Match 4: Crop Dusta Replay Agent (Player 1) vs Opponent (Player 0)
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run([opp_agent, cd_opp.agent])
            r0, r1 = env.steps[-1][0]['reward'], env.steps[-1][1]['reward']
            match_records.append({
                'candidate': 'G_CROP_DUSTA_MACRO',
                'seat': 1,
                'opp': opp_name,
                'seed': seed,
                'cand_score': r1,
                'opp_score': r0,
                'margin': r1 - r0
            })

with open('scratch/causal_study_matches.json', 'w') as f:
    json.dump(match_records, f, indent=2)

print(f"Completed {len(match_records)} matches. Generating summary...")

# Aggregate by candidate
for cand in ['A_V2_BASELINE', 'G_CROP_DUSTA_MACRO']:
    subset = [m for m in match_records if m['candidate'] == cand]
    if subset:
        scores = [m['cand_score'] for m in subset]
        margins = [m['margin'] for m in subset]
        wins = sum(1 for m in subset if m['margin'] > 0)
        print(f"\nCandidate: {cand}")
        print(f"  Matches: {len(subset)}")
        print(f"  Mean Score: ${np.mean(scores):,.1f} +/- ${np.std(scores):,.1f}")
        print(f"  Mean Margin: ${np.mean(margins):+,.1f}")
        print(f"  Win Rate: {wins / len(subset) * 100:.1f}% ({wins}/{len(subset)})")
        print(f"  Min Score: ${np.min(scores):,.1f}, Max Score: ${np.max(scores):,.1f}")
