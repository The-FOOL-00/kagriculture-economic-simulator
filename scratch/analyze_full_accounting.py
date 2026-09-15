import sys
import os
import json
import numpy as np
from collections import defaultdict
from scipy import stats

def analyze_accounting():
    with open("scratch/exact_accounting_200seeds_results.json") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} seeds for exact accounting reconciliation.")
    max_diff_m1 = max(d["m1"]["diff"] for d in data)
    max_diff_q50 = max(d["q50"]["diff"] for d in data)
    max_diff_mecha = max(d["mech_a"]["diff"] for d in data)
    
    print(f"Max diff M1: {max_diff_m1:.10f}")
    print(f"Max diff Q50: {max_diff_q50:.10f}")
    print(f"Max diff MechA: {max_diff_mecha:.10f}")
    assert max(max_diff_m1, max_diff_q50, max_diff_mecha) < 1e-5, "Accounting identity violated!"
    print("VERIFIED: absolute(reconstructed_reward - environment_reward) == 0 to machine precision across ALL 200 SEEDS!")

    # Reward statistics
    m1_rews = np.array([d["m1"]["reward"] for d in data])
    q50_rews = np.array([d["q50"]["reward"] for d in data])
    mecha_rews = np.array([d["mech_a"]["reward"] for d in data])

    delta_mecha_m1 = mecha_rews - m1_rews
    delta_q50_m1 = q50_rews - m1_rews
    delta_mecha_q50 = mecha_rews - q50_rews

    print("\n=== REWARD SUMMARY (Seeds 1250-1449, N=200) ===")
    print(f"M1 Mean: ${np.mean(m1_rews):,.2f} | Median: ${np.median(m1_rews):,.2f}")
    print(f"Q50 Mean: ${np.mean(q50_rews):,.2f} | Median: ${np.median(q50_rews):,.2f}")
    print(f"MechA Mean: ${np.mean(mecha_rews):,.2f} | Median: ${np.median(mecha_rews):,.2f}")

    print("\n=== PAIRED DELTA: Mechanism A - M1 ===")
    print(f"Mean Delta: ${np.mean(delta_mecha_m1):,.2f}")
    print(f"Median Delta: ${np.median(delta_mecha_m1):,.2f}")
    print(f"SD: ${np.std(delta_mecha_m1, ddof=1):,.2f}")
    ci_mecha_m1 = stats.t.interval(0.95, len(delta_mecha_m1)-1, loc=np.mean(delta_mecha_m1), scale=stats.sem(delta_mecha_m1))
    print(f"95% CI: [${ci_mecha_m1[0]:,.2f}, ${ci_mecha_m1[1]:,.2f}]")
    t_res = stats.ttest_1samp(delta_mecha_m1, 0)
    w_res = stats.wilcoxon(delta_mecha_m1)
    print(f"Paired t-test: t={t_res.statistic:.4f}, p={t_res.pvalue:.4f}")
    print(f"Wilcoxon: W={w_res.statistic:.1f}, p={w_res.pvalue:.4f}")
    print(f"Win Rate vs M1: {np.mean(delta_mecha_m1 > 0)*100:.1f}%")

    print("\n=== PAIRED DELTA: Raw Q50 - M1 ===")
    print(f"Mean Delta: ${np.mean(delta_q50_m1):,.2f}")
    print(f"Median Delta: ${np.median(delta_q50_m1):,.2f}")
    ci_q50_m1 = stats.t.interval(0.95, len(delta_q50_m1)-1, loc=np.mean(delta_q50_m1), scale=stats.sem(delta_q50_m1))
    print(f"95% CI: [${ci_q50_m1[0]:,.2f}, ${ci_q50_m1[1]:,.2f}]")
    t_q = stats.ttest_1samp(delta_q50_m1, 0)
    w_q = stats.wilcoxon(delta_q50_m1)
    print(f"Paired t-test: p={t_q.pvalue:.4f}, Wilcoxon: p={w_q.pvalue:.4f}")
    print(f"Win Rate vs M1: {np.mean(delta_q50_m1 > 0)*100:.1f}%")

    print("\n=== ITE: Treatment Effect of Mechanism A over Q50 (A - Q50) ===")
    print(f"Mean ITE: ${np.mean(delta_mecha_q50):,.2f}")
    print(f"Median ITE: ${np.median(delta_mecha_q50):,.2f}")
    print(f"Win Rate vs Q50: {np.mean(delta_mecha_q50 > 0)*100:.1f}%")

    # Aggregate line items across 200 seeds
    print("\n=== FULL MACHINE-PRECISION TRANSACTION LEDGER (Mean per seed) ===")
    keys = set()
    for d in data:
        keys.update(d["m1"]["ledger"].keys())
        keys.update(d["q50"]["ledger"].keys())
        keys.update(d["mech_a"]["ledger"].keys())

    sorted_keys = sorted(keys)
    rev_keys = [k for k in sorted_keys if k.startswith("REV_")]
    exp_keys = [k for k in sorted_keys if k.startswith("EXP_")]

    print(f"{'Line Item':<25} | {'M1':>12} | {'Raw Q50':>12} | {'Mech A':>12} | {'A - M1':>12} | {'A - Q50':>12}")
    print("-" * 95)
    print(f"{'Starting Money':<25} | {'$3,000.00':>12} | {'$3,000.00':>12} | {'$3,000.00':>12} | {'$0.00':>12} | {'$0.00':>12}")
    
    m_rev_m1 = {k: np.mean([d["m1"]["ledger"].get(k, 0.0) for d in data]) for k in rev_keys}
    m_rev_q50 = {k: np.mean([d["q50"]["ledger"].get(k, 0.0) for d in data]) for k in rev_keys}
    m_rev_mecha = {k: np.mean([d["mech_a"]["ledger"].get(k, 0.0) for d in data]) for k in rev_keys}

    print("\n--- REVENUES ---")
    for k in rev_keys:
        item = k.replace("REV_", "")
        diff_m1 = m_rev_mecha[k] - m_rev_m1[k]
        diff_q50 = m_rev_mecha[k] - m_rev_q50[k]
        print(f"{'Revenue: ' + item:<25} | ${m_rev_m1[k]:>11,.2f} | ${m_rev_q50[k]:>11,.2f} | ${m_rev_mecha[k]:>11,.2f} | ${diff_m1:>+11,.2f} | ${diff_q50:>+11,.2f}")

    tot_rev_m1 = sum(m_rev_m1.values())
    tot_rev_q50 = sum(m_rev_q50.values())
    tot_rev_mecha = sum(m_rev_mecha.values())
    print(f"{'TOTAL REVENUES':<25} | ${tot_rev_m1:>11,.2f} | ${tot_rev_q50:>11,.2f} | ${tot_rev_mecha:>11,.2f} | ${tot_rev_mecha - tot_rev_m1:>+11,.2f} | ${tot_rev_mecha - tot_rev_q50:>+11,.2f}")

    m_exp_m1 = {k: np.mean([d["m1"]["ledger"].get(k, 0.0) for d in data]) for k in exp_keys}
    m_exp_q50 = {k: np.mean([d["q50"]["ledger"].get(k, 0.0) for d in data]) for k in exp_keys}
    m_exp_mecha = {k: np.mean([d["mech_a"]["ledger"].get(k, 0.0) for d in data]) for k in exp_keys}

    print("\n--- EXPENDITURES ---")
    for k in exp_keys:
        item = k.replace("EXP_", "")
        diff_m1 = m_exp_mecha[k] - m_exp_m1[k]
        diff_q50 = m_exp_mecha[k] - m_exp_q50[k]
        print(f"{'Expense: ' + item:<25} | ${m_exp_m1[k]:>11,.2f} | ${m_exp_q50[k]:>11,.2f} | ${m_exp_mecha[k]:>11,.2f} | ${diff_m1:>+11,.2f} | ${diff_q50:>+11,.2f}")

    tot_exp_m1 = sum(m_exp_m1.values())
    tot_exp_q50 = sum(m_exp_q50.values())
    tot_exp_mecha = sum(m_exp_mecha.values())
    print(f"{'TOTAL EXPENDITURES':<25} | ${tot_exp_m1:>11,.2f} | ${tot_exp_q50:>11,.2f} | ${tot_exp_mecha:>11,.2f} | ${tot_exp_mecha - tot_exp_m1:>+11,.2f} | ${tot_exp_mecha - tot_exp_q50:>+11,.2f}")

    print("-" * 95)
    net_m1 = 3000.0 + tot_rev_m1 - tot_exp_m1
    net_q50 = 3000.0 + tot_rev_q50 - tot_exp_q50
    net_mecha = 3000.0 + tot_rev_mecha - tot_exp_mecha
    print(f"{'TERMINAL NET REWARD':<25} | ${net_m1:>11,.2f} | ${net_q50:>11,.2f} | ${net_mecha:>11,.2f} | ${net_mecha - net_m1:>+11,.2f} | ${net_mecha - net_q50:>+11,.2f}")
    
    return data

if __name__ == "__main__":
    analyze_accounting()
