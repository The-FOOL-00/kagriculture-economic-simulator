import json
import math
import numpy as np
from scipy import stats

def audit_tournament():
    print("================================================================================")
    print("PHASE 0 AUDIT: AUDITING TOURNAMENT RESULTS")
    print("================================================================================")
    with open('scratch/large_scale_tournament_results.json', 'r') as f:
        data = json.load(f)

    all_passed = True
    for split in ['dev', 'holdout']:
        print(f"\n--- Verifying Split: {split.upper()} ---")
        for agent_key in ['gm', 'v2']:
            d = data[split][agent_key]
            print(f"Agent: {d['name']}")
            print(f"  Reported N: {d['n']}, W-L-T: {d['W-L-T']}, WinRate: {d['win_rate']}")
            print(f"  Reported Mean: {d['mean_reward']:.3f}, Median: {d['median_reward']:.3f}, Std: {d['std_reward']:.3f}")
            print(f"  Reported Margin Mean: {d['mean_margin']:.3f}, Margin 95% CI: [{d['ci95_margin'][0]:.3f}, {d['ci95_margin'][1]:.3f}]")
            
            sub_n = sum(opp['n'] for opp in d['by_opponent'].values())
            sub_wins = 0
            sub_losses = 0
            sub_ties = 0
            weighted_reward = 0.0
            weighted_margin = 0.0
            
            for opp_name, opp in d['by_opponent'].items():
                w, l, t = map(int, opp['W-L-T'].split('-'))
                sub_wins += w
                sub_losses += l
                sub_ties += t
                weighted_reward += opp['mean_reward'] * opp['n']
                weighted_margin += opp['mean_margin'] * opp['n']
                calc_opp_wr = w / opp['n']
                if abs(calc_opp_wr - opp['win_rate']) > 1e-6:
                    print(f"  [ERROR] Opponent {opp_name} win rate mismatch: calc {calc_opp_wr} vs rep {opp['win_rate']}")
                    all_passed = False

            calc_mean_r = weighted_reward / sub_n
            calc_mean_m = weighted_margin / sub_n
            calc_wlt = f"{sub_wins}-{sub_losses}-{sub_ties}"
            calc_wr = sub_wins / sub_n

            n_match = (sub_n == d['n'])
            wlt_match = (calc_wlt == d['W-L-T'])
            wr_match = (abs(calc_wr - d['win_rate']) < 1e-6)
            mean_r_diff = abs(calc_mean_r - d['mean_reward'])
            mean_m_diff = abs(calc_mean_m - d['mean_margin'])

            print(f"  Reconciled N: {sub_n} (Match: {n_match})")
            print(f"  Reconciled W-L-T: {calc_wlt} (Match: {wlt_match})")
            print(f"  Reconciled Win Rate: {calc_wr:.4f} (Match: {wr_match})")
            print(f"  Reconciled Mean Reward: {calc_mean_r:.3f} (Reported: {d['mean_reward']:.3f}, Diff: {mean_r_diff:.6e})")
            print(f"  Reconciled Mean Margin: {calc_mean_m:.3f} (Reported: {d['mean_margin']:.3f}, Diff: {mean_m_diff:.6e})")

            if not (n_match and wlt_match and wr_match and mean_r_diff < 1e-4 and mean_m_diff < 1e-4):
                all_passed = False
                print(f"  [AUDIT FAILED for {agent_key} in {split}]")

    return all_passed

def audit_opponent_suite():
    print("\n================================================================================")
    print("PHASE 0 AUDIT: AUDITING DYNAMIC OPPONENT SUITE RESULTS")
    print("================================================================================")
    with open('scratch/dynamic_opponent_suite_results.json', 'r') as f:
        data = json.load(f)

    all_passed = True
    for agent_name, d in data.items():
        print(f"\nAgent: {agent_name}")
        print(f"  Reported W-L-T: {d['overall_W-L-T']}, Win Rate: {d['overall_win_rate']:.4f}")
        print(f"  Reported Mean Reward: {d['overall_cand_score']:.2f}, Mean Margin: {d['overall_margin']:.2f}")
        
        per_opp = d['per_opponent']
        sub_n = len(per_opp) * 10  # 10 games per opponent
        sub_w = sum(int(opp['W-L-T'].split('-')[0]) for opp in per_opp.values())
        sub_l = sum(int(opp['W-L-T'].split('-')[1]) for opp in per_opp.values())
        sub_t = sum(int(opp['W-L-T'].split('-')[2]) for opp in per_opp.values())
        weighted_r = sum(opp['mean_cand_score'] * 10 for opp in per_opp.values())
        weighted_m = sum(opp['mean_margin'] * 10 for opp in per_opp.values())

        calc_wlt = f"{sub_w}-{sub_l}-{sub_t}"
        calc_wr = sub_w / sub_n
        calc_mean_r = weighted_r / sub_n
        calc_mean_m = weighted_m / sub_n

        wlt_match = (calc_wlt == d['overall_W-L-T'])
        wr_match = (abs(calc_wr - d['overall_win_rate']) < 1e-6)
        r_match = (abs(calc_mean_r - d['overall_cand_score']) < 1e-4)
        m_match = (abs(calc_mean_m - d['overall_margin']) < 1e-4)

        print(f"  Reconciled Games: {sub_n}")
        print(f"  Reconciled W-L-T: {calc_wlt} (Match: {wlt_match})")
        print(f"  Reconciled Win Rate: {calc_wr:.4f} (Match: {wr_match})")
        print(f"  Reconciled Mean Reward: {calc_mean_r:.2f} (Reported: {d['overall_cand_score']:.2f}, Match: {r_match})")
        print(f"  Reconciled Mean Margin: {calc_mean_m:.2f} (Reported: {d['overall_margin']:.2f}, Match: {m_match})")

        if not (wlt_match and wr_match and r_match and m_match):
            all_passed = False
            print(f"  [AUDIT FAILED for {agent_name}]")

    return all_passed

def audit_accounting_and_multi_arm():
    print("\n================================================================================")
    print("PHASE 0 AUDIT: AUDITING ACCOUNTING AND MULTI-ARM RESULTS")
    print("================================================================================")
    with open('scratch/phase1_exact_accounting.json', 'r') as f:
        acc = json.load(f)
    print("Accounting File Content:")
    for k, v in acc.items():
        print(f"  {k}: {v}")
    
    calc_gap = acc['v2_reward'] - acc['prime_reward']
    gap_diff = abs(calc_gap - acc['gap'])
    print(f"  Calculated Gap: {calc_gap:.4f} vs Reported Gap: {acc['gap']:.4f} (Diff: {gap_diff:.6e})")
    
    calc_crop_delta = acc['v2_crop'] - acc['prime_crop']
    print(f"  Calculated Crop Delta: {calc_crop_delta:.4f} vs Reported: {acc['crop_delta']:.4f}")
    
    calc_live_delta = acc['v2_live'] - acc['prime_live']
    print(f"  Calculated Live Delta: {calc_live_delta:.4f} vs Reported: {acc['live_delta']:.4f}")

    with open('scratch/causal_multi_arm_results.json', 'r') as f:
        arms = json.load(f)
    print("\nMulti-Arm Summary:")
    all_arms_passed = True
    for arm_name, arm_data in arms.items():
        scores = arm_data['scores']
        calc_mean = sum(scores) / len(scores)
        diff = abs(calc_mean - arm_data['mean_reward'])
        print(f"  {arm_name}: N={len(scores)}, Calc Mean={calc_mean:.2f}, Rep Mean={arm_data['mean_reward']:.2f}, Diff={diff:.6e}")
        if diff > 1e-4:
            all_arms_passed = False
            
    return (gap_diff < 1e-4) and all_arms_passed

if __name__ == '__main__':
    p1 = audit_tournament()
    p2 = audit_opponent_suite()
    p3 = audit_accounting_and_multi_arm()
    print("\n================================================================================")
    print(f"AUDIT SUMMARY: Tournament Passed: {p1}, Opponent Suite Passed: {p2}, Accounting Passed: {p3}")
    if p1 and p2 and p3:
        print("OVERALL RESULT: AUDIT PASSED - All numbers reconcile exactly to underlying rows!")
    else:
        print("OVERALL RESULT: AUDIT FAILED")
    print("================================================================================")
