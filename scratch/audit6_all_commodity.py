import json
import numpy as np

def run_audit6():
    with open('scratch/final_500seed_qualification_results.json') as f:
        qdata = json.load(f)

    detailed = qdata['detailed']
    seeds = qdata['seeds']
    n = len(seeds)

    commodities = ["STRAWBERRY", "WHEAT", "WOOL", "MILK", "MELON", "FERTILIZER"]

    print("=" * 100)
    print("AUDIT 6: ALL-COMMODITY REGRESSION & DOWNSIDE TAIL AUDIT (500 PAIRED SEEDS)")
    print("=" * 100)

    results = {}
    for comm in commodities:
        rev_key = f"REV_{comm}"
        
        # Revenue deltas
        rev_deltas = np.array([
            detailed['Frozen_Candidate'][str(s)]['ledger'].get(rev_key, 0.0) -
            detailed['Raw_Q50'][str(s)]['ledger'].get(rev_key, 0.0)
            for s in seeds
        ])

        # Quantity deltas
        qty_deltas = np.array([
            detailed['Frozen_Candidate'][str(s)]['sold_qty'].get(comm, 0) -
            detailed['Raw_Q50'][str(s)]['sold_qty'].get(comm, 0)
            for s in seeds
        ])

        mean_rev_d = float(np.mean(rev_deltas))
        med_rev_d = float(np.median(rev_deltas))
        win_rate = float(np.mean(rev_deltas > 0) * 100)
        loss_rate = float(np.mean(rev_deltas < 0) * 100)
        tie_rate = float(np.mean(rev_deltas == 0) * 100)

        min_d = float(np.min(rev_deltas))
        p05 = float(np.percentile(rev_deltas, 5))
        p25 = float(np.percentile(rev_deltas, 25))
        p75 = float(np.percentile(rev_deltas, 75))
        p95 = float(np.percentile(rev_deltas, 95))
        max_d = float(np.max(rev_deltas))

        results[comm] = {
            'mean_revenue_delta': mean_rev_d,
            'median_revenue_delta': med_rev_d,
            'mean_qty_delta': float(np.mean(qty_deltas)),
            'win_rate_pct': win_rate,
            'loss_rate_pct': loss_rate,
            'tie_rate_pct': tie_rate,
            'min': min_d,
            'p05': p05,
            'p25': p25,
            'p75': p75,
            'p95': p95,
            'max': max_d
        }

        print(f"\nCommodity: {comm}")
        print(f"  Mean Rev Delta:   ${mean_rev_d:+8.2f} | Mean Qty Delta: {np.mean(qty_deltas):+5.2f} units")
        print(f"  Median Rev Delta: ${med_rev_d:+8.2f}")
        print(f"  Win / Loss / Tie: {win_rate:5.1f}% / {loss_rate:5.1f}% / {tie_rate:5.1f}%")
        print(f"  Min Delta:        ${min_d:+8.2f}")
        print(f"  Percentiles (5%, 25%, 75%, 95%):")
        print(f"    p05: ${p05:+8.2f} | p25: ${p25:+8.2f} | p75: ${p75:+8.2f} | p95: ${p95:+8.2f}")
        print(f"  Max Delta:        ${max_d:+8.2f}")

    with open('scratch/audit6_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    run_audit6()
