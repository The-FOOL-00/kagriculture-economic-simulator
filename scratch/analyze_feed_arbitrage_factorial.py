"""
Statistical Analysis and Reconciliation for Causal Feed Arbitrage Factorial Study.
Computes rigorous causal main effects, interaction matrices, Wilson CIs, and trajectory breakdowns.
"""

import json
import math
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

def wilson_ci(k, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))) / denom
    return max(0.0, center - half), min(1.0, center + half)

def analyze_results(json_path="scratch/feed_arbitrage_factorial_results.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Total Matches Analyzed: {len(data):,}\n")
    
    # Group by treatment
    by_treatment = {}
    by_t_opp = {}
    
    for row in data:
        t = row["treatment"]
        opp = row["opponent"]
        
        if t not in by_treatment:
            by_treatment[t] = []
        by_treatment[t].append(row)
        
        key = (t, opp)
        if key not in by_t_opp:
            by_t_opp[key] = []
        by_t_opp[key].append(row)
        
    # Table 1: Overall Treatment Performance Table
    print("=" * 140)
    print("TABLE 1: FULL FACTORIAL PERFORMANCE MATRIX (Matched 50 Seeds x 2 Seats = 500 Matches per Treatment)")
    print("=" * 140)
    print(f"{'Candidate / Treatment':<28} | {'Mean Score':>10} | {'Mean Margin':>11} | {'Win Rate (95% CI)':>22} | {'Q3 Step':>8} | {'D10 Cash':>9} | {'WheatBought':>11} | {'Cows':>5} | {'Worst Loss':>11} | {'StdDev':>8}")
    print("-" * 140)
    
    summary_stats = {}
    
    for t, rows in by_treatment.items():
        scores = [r["reward_us"] for r in rows]
        margins = [r["margin"] for r in rows]
        wins = sum(r["won"] for r in rows)
        n = len(rows)
        wr = wins / n
        ci_l, ci_u = wilson_ci(wins, n)
        
        q3_steps = [r["q3_step"] for r in rows]
        d10_cashes = [r["cp_cash"].get("cash_240", 0) for r in rows]
        wheat_boughts = [r["wheat_bought"] for r in rows]
        cows = [r["final_cows"] for r in rows]
        worst_loss = min(margins)
        std_score = np.std(scores)
        
        summary_stats[t] = {
            "mean_score": np.mean(scores),
            "mean_margin": np.mean(margins),
            "win_rate": wr,
            "ci_l": ci_l,
            "ci_u": ci_u,
            "mean_q3": np.mean(q3_steps),
            "mean_d10_cash": np.mean(d10_cashes),
            "mean_wheat": np.mean(wheat_boughts),
            "mean_cows": np.mean(cows),
            "worst_loss": worst_loss,
            "std_score": std_score,
            "n": n
        }
        
        ci_str = f"{wr*100:5.1f}% [{ci_l*100:4.1f}%-{ci_u*100:4.1f}%]"
        print(f"{t:<28} | ${np.mean(scores):9.1f} | ${np.mean(margins):+10.1f} | {ci_str:>22} | {np.mean(q3_steps):8.1f} | ${np.mean(d10_cashes):8.1f} | {np.mean(wheat_boughts):11.1f} | {np.mean(cows):5.1f} | ${worst_loss:+10.1f} | ${std_score:7.1f}")
        
    print("-" * 140)
    
    # Table 2: Breakdown by Opponent Archetype
    opponents = sorted(list(set(r["opponent"] for r in data)))
    print("\n" + "=" * 140)
    print("TABLE 2: SCORE BREAKDOWN BY OPPONENT ARCHETYPE")
    print("=" * 140)
    header = f"{'Candidate / Treatment':<28} | " + " | ".join([f"{opp:>18}" for opp in opponents])
    print(header)
    print("-" * len(header))
    
    for t in by_treatment:
        line = f"{t:<28} | "
        for opp in opponents:
            rows = by_t_opp.get((t, opp), [])
            mean_s = np.mean([r["reward_us"] for r in rows]) if rows else 0
            mean_m = np.mean([r["margin"] for r in rows]) if rows else 0
            line += f"${mean_s:8.1f} ({mean_m:+7.0f}) | "
        print(line[:-3])
    print("-" * len(header))
    
    # Table 3: Rigorous Causal Effect Decomposition
    print("\n" + "=" * 140)
    print("TABLE 3: RIGOROUS CAUSAL MAIN EFFECTS AND INTERACTION TERMS (Relative to Base V2)")
    print("=" * 140)
    
    base_s = summary_stats.get("A_BASE_V2", {}).get("mean_score", 0)
    base_m = summary_stats.get("A_BASE_V2", {}).get("mean_margin", 0)
    
    delta_B_s = summary_stats.get("B_DYN_LIQ", {}).get("mean_score", base_s) - base_s
    delta_C_s = summary_stats.get("C_EXT_WHEAT", {}).get("mean_score", base_s) - base_s
    delta_D10_s = summary_stats.get("D_COWS_10", {}).get("mean_score", base_s) - base_s
    delta_D12_s = summary_stats.get("D_COWS_12", {}).get("mean_score", base_s) - base_s
    delta_D13_s = summary_stats.get("D_COWS_13", {}).get("mean_score", base_s) - base_s
    
    delta_E_s = summary_stats.get("E_LIQ_WHEAT", {}).get("mean_score", base_s) - base_s
    delta_F_s = summary_stats.get("F_LIQ_COWS", {}).get("mean_score", base_s) - base_s
    delta_G_s = summary_stats.get("G_WHEAT_COWS", {}).get("mean_score", base_s) - base_s
    delta_H12_s = summary_stats.get("H_ALL_THREE_12C", {}).get("mean_score", base_s) - base_s
    delta_H13_s = summary_stats.get("H_ALL_THREE_13C", {}).get("mean_score", base_s) - base_s
    
    # Interactions
    inter_BC = delta_E_s - (delta_B_s + delta_C_s)
    inter_BD12 = delta_F_s - (delta_B_s + delta_D12_s)
    inter_CD12 = delta_G_s - (delta_C_s + delta_D12_s)
    inter_BCD12 = delta_H12_s - (delta_B_s + delta_C_s + delta_D12_s + inter_BC + inter_BD12 + inter_CD12)
    
    print(f"Baseline V2 Score:                                ${base_s:9.1f}")
    print(f"Main Effect: Dynamic Liquidation (ΔB):            ${delta_B_s:+9.1f}")
    print(f"Main Effect: External Wheat Feed (ΔC):            ${delta_C_s:+9.1f}")
    print(f"Main Effect: 10 Cows (ΔD10):                      ${delta_D10_s:+9.1f}")
    print(f"Main Effect: 12 Cows (ΔD12):                      ${delta_D12_s:+9.1f}")
    print(f"Main Effect: 13 Cows (ΔD13):                      ${delta_D13_s:+9.1f}")
    print(f"2-Way Interaction: I(DynLiq, ExtWheat) [I(B,C)]:  ${inter_BC:+9.1f}")
    print(f"2-Way Interaction: I(DynLiq, 12Cows)   [I(B,D)]:  ${inter_BD12:+9.1f}")
    print(f"2-Way Interaction: I(ExtWheat, 12Cows) [I(C,D)]:  ${inter_CD12:+9.1f}")
    print(f"3-Way Interaction: I(B, C, D12):                  ${inter_BCD12:+9.1f}")
    print(f"Total Observed Shift in H (All Three 12C):        ${delta_H12_s:+9.1f} (Score: ${summary_stats.get('H_ALL_THREE_12C', {}).get('mean_score', 0):9.1f})")
    print(f"Total Observed Shift in H (All Three 13C):        ${delta_H13_s:+9.1f} (Score: ${summary_stats.get('H_ALL_THREE_13C', {}).get('mean_score', 0):9.1f})")
    print("=" * 140)

if __name__ == "__main__":
    analyze_results()
