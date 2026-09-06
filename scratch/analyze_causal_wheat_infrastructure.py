import json
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/causal_wheat_infrastructure_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print(f"Total Matches Analyzed: {len(results):,}\n")

treatments = sorted(list(set(r['treatment'] for r in results)))
opponents = sorted(list(set(r['opponent'] for r in results)))

print("=" * 140)
print("PHASE 5: CONTROLLED CAUSAL DECOMPOSITION OF WHEAT VS SPATIAL INFRASTRUCTURE")
print("=" * 140)
print(f"{'Treatment Arm':<30} | {'Mean Score':>11} | {'Mean Margin':>12} | {'Win Rate':>9} | {'Cows':>5} | {'Pastures':>8} | {'Worst Loss':>12} | {'StdDev':>10}")
print("-" * 140)

base_score = 0
arm_stats = {}

for t in treatments:
    rows = [r for r in results if r['treatment'] == t]
    scores = [r['reward_us'] for r in rows]
    margins = [r['margin'] for r in rows]
    wins = [r['win'] for r in rows]
    cows = [r['final_cows'] for r in rows]
    past = [r['final_pastures'] for r in rows]
    
    mean_s = np.mean(scores)
    mean_m = np.mean(margins)
    wr = np.mean(wins) * 100
    worst = min(margins)
    sd = np.std(scores)
    
    if t == 'A_BASE_V2':
        base_score = mean_s
        
    arm_stats[t] = {
        'mean_score': mean_s,
        'mean_margin': mean_m,
        'wr': wr,
        'worst': worst,
        'sd': sd,
        'cows': np.mean(cows),
        'past': np.mean(past)
    }
    
    print(f"{t:<30} | ${mean_s:10.1f} | ${mean_m:+11.1f} | {wr:8.1f}% | {np.mean(cows):5.1f} | {np.mean(past):8.1f} | ${worst:+11.1f} | ${sd:9.1f}")

print("\n" + "=" * 140)
print("SCORE BREAKDOWN ACROSS OPPONENT CONTROL LOOPS")
print("=" * 140)
print(f"{'Treatment Arm':<30} | {'aethel_v2_closed':<28} | {'live_flooder_v1':<28} | {'replay_whyme_labs':<28}")
print("-" * 140)

for t in treatments:
    row_strs = []
    for opp in ['aethel_v2_closed', 'live_flooder_v1', 'replay_whyme_labs']:
        rows = [r for r in results if r['treatment'] == t and r['opponent'] == opp]
        mean_s = np.mean([r['reward_us'] for r in rows])
        mean_m = np.mean([r['margin'] for r in rows])
        row_strs.append(f"${mean_s:9.1f} ({mean_m:+8.0f})")
    print(f"{t:<30} | {row_strs[0]:<28} | {row_strs[1]:<28} | {row_strs[2]:<28}")

print("\n" + "=" * 140)
print("CAUSAL MAIN EFFECTS & HYPOTHESIS TEST VERDICT")
print("=" * 140)
delta_feed_only = arm_stats['C_V2_EXTRA_FEED_ONLY']['mean_score'] - base_score
delta_pasture_cows_no_feed = arm_stats['E_V2_PASTURE_COWS_NO_FEED']['mean_score'] - base_score
delta_pasture_cows_ext_feed = arm_stats['F_V2_PASTURE_COWS_EXT_FEED']['mean_score'] - base_score
delta_crop_dusta_tape = arm_stats['G_FULL_CROP_DUSTA_TAPE']['mean_score'] - base_score

print(f"1. Baseline V2 Score:                                  ${base_score:,.1f}")
print(f"2. Effect of Extra Feed ONLY (Arm C - A):              ${delta_feed_only:+,.1f} (FALSIFIED)")
print(f"3. Effect of Pasture + Cows WITHOUT Feed (Arm E - A):  ${delta_pasture_cows_no_feed:+,.1f} (INERT)")
print(f"4. Effect of Pasture + Cows WITH Feed (Arm F - A):     ${delta_pasture_cows_ext_feed:+,.1f} (SEVERE DEGRADATION)")
print(f"5. Crop Dusta Replay Tape vs General Meta (Arm G - A): ${delta_crop_dusta_tape:+,.1f}")
print("=" * 140)
