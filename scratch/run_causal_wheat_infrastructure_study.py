"""
Phase 5: Controlled Causal Decomposition of Wheat vs Spatial Infrastructure.
Arms:
A: Baseline V2
B: V2 + same livestock (8C/6S), zero extra feed purchase
C: V2 + extra feed purchase (high buy rate), same livestock (8C/6S)
D: V2 + 16 pastures infrastructure, same livestock (8C/6S)
E: V2 + 16 pastures + 12 Cows, growing own feed
F: V2 + 16 pastures + 12 Cows + external wheat feed
G: Full Reconstructed Crop Dusta Macro Sequence
"""

import sys
import os
import json
import time
import numpy as np
from multiprocessing import Pool, cpu_count

sys.path.insert(0, '.')
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as flooder
import opponents.replay_crop_dusta as replay_cd
import opponents.replay_whyme_labs as replay_whyme
import scratch.causal_feed_arbitrage_agents as causal

# Define the 7 experimental arms
# Arm A: v2.agent
# Arm B: causal.agent_A (baseline V2)
# Arm C: causal.agent_C (ext wheat only, 8 cows)
# Arm D: causal.agent_D12 (12 cows capability, no extra feed forced)
# Arm E: causal.agent_F (dyn liq + 12 cows)
# Arm F: causal.agent_H12 (all three: 12 cows + ext wheat + dyn liq)
# Arm G: replay_cd.agent (Crop Dusta tape replay)

TREATMENTS = {
    'A_BASE_V2': v2.agent,
    'B_V2_NO_EXTRA_FEED': causal.agent_A,
    'C_V2_EXTRA_FEED_ONLY': causal.agent_C,
    'D_V2_EXTRA_PASTURE_12C': causal.agent_D12,
    'E_V2_PASTURE_COWS_NO_FEED': causal.agent_F,
    'F_V2_PASTURE_COWS_EXT_FEED': causal.agent_H,
    'G_FULL_CROP_DUSTA_TAPE': replay_cd.agent
}

OPPONENTS = {
    'aethel_v2_closed': v2.agent,
    'live_flooder_v1': flooder.agent,
    'replay_whyme_labs': replay_whyme.agent
}

SEEDS = [1000 + i * 37 for i in range(25)] # 25 paired seeds x 2 seats = 50 matches per pair

def run_match(task):
    t_name, opp_name, seed, seat = task
    t_agent = TREATMENTS[t_name]
    opp_agent = OPPONENTS[opp_name]
    
    if seat == 0:
        agents = [t_agent, opp_agent]
    else:
        agents = [opp_agent, t_agent]
        
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(agents)
        steps = env.steps
        r0 = float(steps[-1][0]['reward'] or 0)
        r1 = float(steps[-1][1]['reward'] or 0)
        
        r_us = r0 if seat == 0 else r1
        r_opp = r1 if seat == 0 else r0
        margin = r_us - r_opp
        win = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
        
        # Telemetry
        farm_us = steps[-1][seat]['observation']['farms'][seat]
        cows = sum(1 for row in farm_us.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
        past = sum(1 for row in farm_us.get('tiles', []) for t in row if isinstance(t, dict) and t.get('kind') == 'PASTURE')
        
        return {
            'treatment': t_name,
            'opponent': opp_name,
            'seed': seed,
            'seat': seat,
            'reward_us': r_us,
            'reward_opp': r_opp,
            'margin': margin,
            'win': win,
            'final_cows': cows,
            'final_pastures': past
        }
    except Exception as e:
        return {
            'treatment': t_name,
            'opponent': opp_name,
            'seed': seed,
            'seat': seat,
            'error': str(e),
            'reward_us': 0,
            'reward_opp': 0,
            'margin': 0,
            'win': 0,
            'final_cows': 0,
            'final_pastures': 0
        }

if __name__ == '__main__':
    tasks = []
    for t_name in TREATMENTS:
        for opp_name in OPPONENTS:
            for seed in SEEDS:
                for seat in [0, 1]:
                    tasks.append((t_name, opp_name, seed, seat))
                    
    print(f"Total Matches to run: {len(tasks)} (Treatments: {len(TREATMENTS)}, Opponents: {len(OPPONENTS)}, Matches per pair: {len(SEEDS)*2})")
    
    workers = min(12, cpu_count())
    t0 = time.time()
    with Pool(workers) as p:
        results = p.map(run_match, tasks)
    t1 = time.time()
    
    print(f"Completed {len(results)} matches in {t1-t0:.1f}s")
    
    # Save results
    with open('scratch/causal_wheat_infrastructure_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print("Saved results to scratch/causal_wheat_infrastructure_results.json")
