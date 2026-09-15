import json
import numpy as np

def run_tail_and_accounting_audit():
    with open('scratch/final_500seed_qualification_results.json') as f:
        data = json.load(f)

    seeds = data['seeds']
    cand_dict = data['detailed']['Frozen_Candidate']
    q50_dict = data['detailed']['Raw_Q50']
    m1_dict = data['detailed']['M1_Baseline']

    deltas = []
    wins = 0
    losses = 0
    ties = 0

    mismatches = []

    # Check accounting identity for all runs
    for p_name, p_dict in [('M1', m1_dict), ('Q50', q50_dict), ('Candidate', cand_dict)]:
        for s in seeds:
            info = p_dict[str(s)]
            rew = info['reward']
            led = info['ledger']
            
            init_cash = 1000.0
            revs = sum(v for k, v in led.items() if k.startswith('REV_'))
            exps = sum(v for k, v in led.items() if k.startswith('EXP_'))
            reconstructed = init_cash + revs - exps
            err = abs(reconstructed - rew)
            if err > 1e-6:
                mismatches.append((p_name, s, rew, reconstructed, err))

    print(f"Accounting verification across all 1500 runs: {len(mismatches)} mismatches (err > 1e-6)")
    if mismatches:
        print("First mismatch:", mismatches[0])

    seed_delta_pairs = []
    for s in seeds:
        c_rew = cand_dict[str(s)]['reward']
        q_rew = q50_dict[str(s)]['reward']
        d = c_rew - q_rew
        deltas.append(d)
        seed_delta_pairs.append((s, d))
        if d > 0:
            wins += 1
        elif d < 0:
            losses += 1
        else:
            ties += 1

    deltas = np.array(deltas)
    seed_delta_pairs.sort(key=lambda x: x[1])

    print("\n=== PHASE 3 EXACT METRICS ===")
    print(f"Mean delta: +${np.mean(deltas):.2f}")
    print(f"Median delta: +${np.median(deltas):.2f}")
    print(f"SD delta: ${np.std(deltas):.2f}")
    print(f"Win rate: {wins / len(deltas) * 100:.1f}%")
    print(f"Wins: {wins}, Losses: {losses}, Ties: {ties}")
    print(f"Min delta: ${np.min(deltas):.2f} (Seed {seed_delta_pairs[0][0]})")
    print(f"Max delta: ${np.max(deltas):.2f} (Seed {seed_delta_pairs[-1][0]})")

    print("\n=== PHASE 4 TAIL-RISK ANALYSIS ===")
    n = len(deltas)
    print(f"Total seeds: {n}")
    
    # Threshold probabilities
    c_lt_0 = int(np.sum(deltas < 0))
    c_lt_1k = int(np.sum(deltas < -1000))
    c_lt_5k = int(np.sum(deltas < -5000))
    c_lt_10k = int(np.sum(deltas < -10000))
    c_lt_20k = int(np.sum(deltas < -20000))

    print(f"P(delta < $0):      {c_lt_0/n*100:.2f}% ({c_lt_0}/{n})")
    print(f"P(delta < -$1,000):  {c_lt_1k/n*100:.2f}% ({c_lt_1k}/{n})")
    print(f"P(delta < -$5,000):  {c_lt_5k/n*100:.2f}% ({c_lt_5k}/{n})")
    print(f"P(delta < -$10,000): {c_lt_10k/n*100:.2f}% ({c_lt_10k}/{n})")
    print(f"P(delta < -$20,000): {c_lt_20k/n*100:.2f}% ({c_lt_20k}/{n})")

    print("\nWorst 10 seeds & deltas:")
    for s, d in seed_delta_pairs[:10]:
        print(f"  Seed {s}: ${d:+.2f}")

    print("\nBest 10 seeds & deltas:")
    for s, d in seed_delta_pairs[-10:]:
        print(f"  Seed {s}: ${d:+.2f}")

    # Summary statistics for quantile slices
    for label, count in [("Worst 10", 10), ("Worst 25", 25), ("Worst 50", 50), ("Worst 100", 100),
                         ("Best 10", 10), ("Best 25", 25), ("Best 50", 50), ("Best 100", 100)]:
        if label.startswith("Worst"):
            sub = [d for s, d in seed_delta_pairs[:count]]
        else:
            sub = [d for s, d in seed_delta_pairs[-count:]]
        print(f"{label:<10}: Mean = ${np.mean(sub):+10.2f}, Median = ${np.median(sub):+10.2f}, Min = ${np.min(sub):+10.2f}, Max = ${np.max(sub):+10.2f}")

    # Catastrophic losses analysis (< -$10,000)
    catastrophic = [pair for pair in seed_delta_pairs if pair[1] < -10000]
    print(f"\nCatastrophic losses (< -$10,000): {len(catastrophic)}")
    for s, d in catastrophic:
        c_led = cand_dict[str(s)]['ledger']
        q_led = q50_dict[str(s)]['ledger']
        print(f"\n--- Forensics on Catastrophic Seed {s} (Delta: ${d:+.2f}) ---")
        all_k = set(c_led.keys()) | set(q_led.keys())
        for k in sorted(all_k):
            cv = c_led.get(k, 0)
            qv = q_led.get(k, 0)
            diff = cv - qv
            if abs(diff) > 100:
                print(f"  {k:<20}: Q50 = ${qv:10.2f} | Cand = ${cv:10.2f} | Diff = ${diff:+10.2f}")

    print("\n=== PHASE 8 EXACT FINANCIAL DOLLAR BRIDGE ===")
    # Aggregate ledger components across all 500 seeds
    all_keys = sorted(list(set(k for s in seeds for k in cand_dict[str(s)]['ledger'].keys()) |
                           set(k for s in seeds for k in q50_dict[str(s)]['ledger'].keys())))
    
    bridge = {}
    print(f"{'Ledger Component':<25} | {'Mean Q50 ($)':<12} | {'Mean Cand ($)':<12} | {'Delta ($)':<12}")
    print("-" * 70)
    total_delta = 0.0
    for k in all_keys:
        q_mean = np.mean([q50_dict[str(s)]['ledger'].get(k, 0.0) for s in seeds])
        c_mean = np.mean([cand_dict[str(s)]['ledger'].get(k, 0.0) for s in seeds])
        if k.startswith('REV_'):
            comp_delta = c_mean - q_mean
        elif k.startswith('EXP_'):
            comp_delta = -(c_mean - q_mean)
        else:
            comp_delta = c_mean - q_mean
        total_delta += comp_delta
        bridge[k] = (q_mean, c_mean, comp_delta)
        if abs(comp_delta) > 0.01:
            print(f"{k:<25} | ${q_mean:10.2f}  | ${c_mean:10.2f}  | ${comp_delta:+10.2f}")
    
    print("-" * 70)
    print(f"{'TOTAL BRIDGE DELTA':<25} |               |               | ${total_delta:+10.2f}")
    print(f"{'ENVIRONMENT MEAN DELTA':<25} |               |               | ${np.mean(deltas):+10.2f}")
    print(f"{'BRIDGE DISCREPANCY':<25} |               |               | ${abs(total_delta - np.mean(deltas)):.8f}")

if __name__ == '__main__':
    run_tail_and_accounting_audit()
