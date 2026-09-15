import json
import numpy as np
from scipy import stats

def run_audit4():
    with open('scratch/final_500seed_qualification_results.json') as f:
        qdata = json.load(f)

    detailed = qdata['detailed']
    seeds = qdata['seeds']

    records = []
    for s in seeds:
        s_str = str(s)
        c_rew = detailed['Frozen_Candidate'][s_str]['reward']
        q_rew = detailed['Raw_Q50'][s_str]['reward']
        d = c_rew - q_rew
        records.append({'seed': s, 'q_rew': q_rew, 'c_rew': c_rew, 'delta': d})

    # Sort by q_rew to form quartiles
    records.sort(key=lambda x: x['q_rew'])
    n_total = len(records)
    q_size = n_total // 4
    
    partitions = {
        'Q1 (Lowest Baseline)': records[:q_size],
        'Q2 (Lower-Mid Baseline)': records[q_size:2*q_size],
        'Q3 (Upper-Mid Baseline)': records[2*q_size:3*q_size],
        'Q4 (Highest Baseline)': records[3*q_size:]
    }

    print("=" * 80)
    print("AUDIT 4: CONDITIONAL-STABILITY CLAIMS ACROSS BASELINE QUARTILES")
    print("=" * 80)

    results = {}
    for name, part in partitions.items():
        deltas = np.array([r['delta'] for r in part])
        n = len(deltas)
        mean_d = float(np.mean(deltas))
        med_d = float(np.median(deltas))
        sd_d = float(np.std(deltas, ddof=1))
        
        # Bootstrap CI (10,000 resamples)
        rng = np.random.default_rng(42)
        boot_means = [np.mean(rng.choice(deltas, size=n, replace=True)) for _ in range(10000)]
        ci_low = float(np.percentile(boot_means, 2.5))
        ci_high = float(np.percentile(boot_means, 97.5))
        
        wins = int(np.sum(deltas > 0))
        ties = int(np.sum(deltas == 0))
        losses = int(np.sum(deltas < 0))
        
        pct_loss_500 = float(np.mean(deltas < -500) * 100)
        pct_loss_1000 = float(np.mean(deltas < -1000) * 100)
        worst_loss = float(np.min(deltas))
        
        results[name] = {
            'N': n,
            'q_rew_range': [part[0]['q_rew'], part[-1]['q_rew']],
            'mean_delta': mean_d,
            'median_delta': med_d,
            'std_dev': sd_d,
            'ci95': [ci_low, ci_high],
            'wins': wins,
            'ties': ties,
            'losses': losses,
            'win_rate_pct': float(wins / n * 100),
            'pct_loss_gt_500': pct_loss_500,
            'pct_loss_gt_1000': pct_loss_1000,
            'worst_loss': worst_loss
        }

        print(f"\nPartition: {name} (N={n}, Baseline Range: [${part[0]['q_rew']:,.0f}, ${part[-1]['q_rew']:,.0f}])")
        print(f"  Mean Delta:        ${mean_d:+,.2f} (95% CI: [${ci_low:+,.2f}, ${ci_high:+,.2f}])")
        print(f"  Median Delta:      ${med_d:+,.2f}")
        print(f"  Std Dev:           ${sd_d:,.2f}")
        print(f"  Win / Tie / Loss:  {wins} / {ties} / {losses} (Win Rate: {wins/n*100:.1f}%)")
        print(f"  Losses < -$500:    {pct_loss_500:.1f}%")
        print(f"  Losses < -$1,000:  {pct_loss_1000:.1f}%")
        print(f"  Worst Loss:        ${worst_loss:+,.2f}")

    with open('scratch/audit4_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    run_audit4()
