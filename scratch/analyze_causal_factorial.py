"""
=============================================================================
CAUSAL FACTORIAL DATA ANALYSIS & STATISTICAL AUDIT
=============================================================================
Parses raw simulation telemetry and computes:
- Q3 Affordability / Satisfiability % at T216
- Actual Q3 unlock step
- Trajectory cash at Day 5, 9, 10, 15, 20, 25, 30
- Win rate & Wilson Score 95% Confidence Intervals
- Causal Main Effects: Delta(Q3), Delta(Shop), Delta(Livestock)
- Interaction terms: I(Q3, Shop), I(Q3, Livestock), I(Shop, Livestock)
- Hypothesis falsification / verification tests
=============================================================================
"""

import os
import sys
import json
import math
import numpy as np

def wilson_interval(wins, total, confidence=0.95):
    if total == 0:
        return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0


def analyze_results(json_path=r"c:\Users\Sundareswaran\Kagriculture\scratch\causal_factorial_raw_results.json"):
    with open(json_path, "r") as fp:
        raw_data = json.load(fp)
        
    print(f"Loaded {len(raw_data)} matches from {json_path}\n")
    
    # Organize by (treatment, opponent)
    treatments = ["BASE_V2", "Q3_ONLY", "SHOP_ONLY", "LIVESTOCK_ONLY", "Q3_SHOP", "Q3_LIVESTOCK", "SHOP_LIVESTOCK", "FULL_FACTORIAL"]
    opponents = ["live_flooder_v1", "aethel_v1_titan", "replay_crop_dusta", "replay_kawatta_taido"]
    
    matrix = {t: {o: [] for o in opponents} for t in treatments}
    for row in raw_data:
        t = row["t_key"]
        o = row["opp_key"]
        if t in matrix and o in matrix[t]:
            matrix[t][o].append(row)
            
    # -----------------------------------------------------------------------
    # 1. Q3 VELOCITY ANALYSIS (Turn 216 Satisfiability & Actual Unlock)
    # -----------------------------------------------------------------------
    print("=" * 90)
    print("SECTION 1: Q3 VELOCITY SATISFIABILITY & AFFORDABILITY AUDIT")
    print("=" * 90)
    
    for o in opponents:
        base_rows = matrix["BASE_V2"][o]
        q3_rows = matrix["Q3_ONLY"][o]
        
        m216_base = [r["m_216"] for r in base_rows]
        afford_base = sum(1 for m in m216_base if m >= 4000)
        
        q3_steps_base = [r["actual_q3_step"] for r in base_rows if r["actual_q3_step"] is not None]
        q3_steps_q3only = [r["actual_q3_step"] for r in q3_rows if r["actual_q3_step"] is not None]
        
        early_unlocked = sum(1 for s in q3_steps_q3only if s <= 216)
        
        print(f"Opponent: {o}")
        print(f"  * Base V2 Cash at T216: Mean=${np.mean(m216_base):.1f} +/- ${np.std(m216_base):.1f} (Min=${np.min(m216_base):.1f}, Max=${np.max(m216_base):.1f})")
        print(f"  * P(Cash >= $4,000 at T216): {afford_base}/{len(base_rows)} ({afford_base/len(base_rows)*100:.1f}%)")
        print(f"  * Base V2 Mean Q3 Unlock Step: {np.mean(q3_steps_base):.1f} (Median: {np.median(q3_steps_base):.0f})")
        print(f"  * Q3-Only Early Unlock (<Step 217): {early_unlocked}/{len(q3_rows)} ({early_unlocked/len(q3_rows)*100:.1f}%)")
        print(f"  * Q3-Only Mean Q3 Unlock Step: {np.mean(q3_steps_q3only):.1f} (Median: {np.median(q3_steps_q3only):.0f})")
        print()
        
    # -----------------------------------------------------------------------
    # 2. OVERALL MACROECONOMIC SUMMARY TABLE (Cash, Margin, WinRate)
    # -----------------------------------------------------------------------
    print("=" * 90)
    print("SECTION 2: TREATMENT PERFORMANCE ACROSS ALL OPPONENTS")
    print("=" * 90)
    
    summary_stats = {}
    
    for t in treatments:
        all_t_rows = []
        for o in opponents:
            all_t_rows.extend(matrix[t][o])
            
        wins = sum(r["win"] for r in all_t_rows)
        total = len(all_t_rows)
        wr = wins / total * 100.0
        w_low, w_high = wilson_interval(wins, total)
        
        rewards_us = [r["final_us"] for r in all_t_rows]
        rewards_opp = [r["final_opp"] for r in all_t_rows]
        margins = [r["margin"] for r in all_t_rows]
        
        m_d5 = [r["m_120"] for r in all_t_rows]
        m_d10 = [r["m_240"] for r in all_t_rows]
        m_d15 = [r["m_360"] for r in all_t_rows]
        m_d20 = [r["m_480"] for r in all_t_rows]
        m_d25 = [r["m_600"] for r in all_t_rows]
        
        summary_stats[t] = {
            "win_rate": wr,
            "ci_low": w_low,
            "ci_high": w_high,
            "mean_reward": np.mean(rewards_us),
            "std_reward": np.std(rewards_us),
            "mean_margin": np.mean(margins),
            "std_margin": np.std(margins),
            "mean_opp": np.mean(rewards_opp),
            "d5_cash": np.mean(m_d5),
            "d10_cash": np.mean(m_d10),
            "d15_cash": np.mean(m_d15),
            "d20_cash": np.mean(m_d20),
            "d25_cash": np.mean(m_d25),
        }
        
        print(f"[{t:16s}] WinRate: {wr:5.1f}% [{w_low:4.1f}% - {w_high:4.1f}%] | Mean Score: ${np.mean(rewards_us):9.1f} | Net Margin: ${np.mean(margins):+9.1f} | D10 Cash: ${np.mean(m_d10):6.1f} | D15 Cash: ${np.mean(m_d15):7.1f}")
        
    print()
    
    # -----------------------------------------------------------------------
    # 3. OPPONENT-BY-OPPONENT BREAKDOWN
    # -----------------------------------------------------------------------
    print("=" * 90)
    print("SECTION 3: OPPONENT-BY-OPPONENT SCORE & MARGIN MATRIX")
    print("=" * 90)
    
    header = f"{'Treatment':16s}"
    for o in opponents:
        header += f" | {o[:14]:14s} (Us / Opp / Net)"
    print(header)
    print("-" * len(header))
    
    for t in treatments:
        row_str = f"{t:16s}"
        for o in opponents:
            rows = matrix[t][o]
            m_us = np.mean([r["final_us"] for r in rows])
            m_op = np.mean([r["final_opp"] for r in rows])
            m_net = np.mean([r["margin"] for r in rows])
            row_str += f" | ${m_us/1000:4.1f}k/${m_op/1000:4.1f}k/${m_net/1000:+5.1f}k"
        print(row_str)
        
    print()
    
    # -----------------------------------------------------------------------
    # 4. CAUSAL MAIN EFFECTS & INTERACTION CALCULATIONS
    # -----------------------------------------------------------------------
    print("=" * 90)
    print("SECTION 4: STRICT CAUSAL MAIN EFFECTS & INTERACTION TERMS")
    print("=" * 90)
    
    base_score = summary_stats["BASE_V2"]["mean_reward"]
    base_margin = summary_stats["BASE_V2"]["mean_margin"]
    
    # Main Effects (on reward)
    delta_q3 = summary_stats["Q3_ONLY"]["mean_reward"] - base_score
    delta_shop = summary_stats["SHOP_ONLY"]["mean_reward"] - base_score
    delta_ls = summary_stats["LIVESTOCK_ONLY"]["mean_reward"] - base_score
    
    # Main Effects (on margin)
    delta_q3_m = summary_stats["Q3_ONLY"]["mean_margin"] - base_margin
    delta_shop_m = summary_stats["SHOP_ONLY"]["mean_margin"] - base_margin
    delta_ls_m = summary_stats["LIVESTOCK_ONLY"]["mean_margin"] - base_margin
    
    print(f"BASELINE SCORE (Frozen V2): ${base_score:.1f} (Net Margin: ${base_margin:+.1f})")
    print()
    print("ISOLATED MAIN EFFECTS:")
    print(f"  * Delta(Q3 Velocity Only)     : ${delta_q3:+8.1f} Reward | ${delta_q3_m:+8.1f} Net Margin")
    print(f"  * Delta(Shop Sync Only)       : ${delta_shop:+8.1f} Reward | ${delta_shop_m:+8.1f} Net Margin")
    print(f"  * Delta(Livestock Spec Only)  : ${delta_ls:+8.1f} Reward | ${delta_ls_m:+8.1f} Net Margin")
    print()
    
    # Two-Way Interaction Terms
    # I(A, B) = [Score(A+B) - Base] - [Delta(A) + Delta(B)]
    actual_q3_shop = summary_stats["Q3_SHOP"]["mean_reward"] - base_score
    i_q3_shop = actual_q3_shop - (delta_q3 + delta_shop)
    
    actual_q3_ls = summary_stats["Q3_LIVESTOCK"]["mean_reward"] - base_score
    i_q3_ls = actual_q3_ls - (delta_q3 + delta_ls)
    
    actual_shop_ls = summary_stats["SHOP_LIVESTOCK"]["mean_reward"] - base_score
    i_shop_ls = actual_shop_ls - (delta_shop + delta_ls)
    
    print("TWO-WAY INTERACTION EFFECTS:")
    print(f"  * Joint Gain (Q3 + Shop)       : Actual=${actual_q3_shop:+8.1f} vs Additive=${delta_q3+delta_shop:+8.1f} -> Interaction I(Q3, Shop)      = ${i_q3_shop:+8.1f}")
    print(f"  * Joint Gain (Q3 + Livestock)  : Actual=${actual_q3_ls:+8.1f} vs Additive=${delta_q3+delta_ls:+8.1f} -> Interaction I(Q3, Livestock) = ${i_q3_ls:+8.1f}")
    print(f"  * Joint Gain (Shop + Livestock): Actual=${actual_shop_ls:+8.1f} vs Additive=${delta_shop+delta_ls:+8.1f} -> Interaction I(Shop, Livestock) = ${i_shop_ls:+8.1f}")
    print()
    
    # Three-Way Full Factorial Interaction
    actual_full = summary_stats["FULL_FACTORIAL"]["mean_reward"] - base_score
    additive_full = delta_q3 + delta_shop + delta_ls + i_q3_shop + i_q3_ls + i_shop_ls
    i_full = actual_full - additive_full
    
    print("THREE-WAY FULL FACTORIAL EFFECT:")
    print(f"  * Full Factorial Gain (Q3 + Shop + LS): Actual=${actual_full:+8.1f} vs Additive=${delta_q3+delta_shop+delta_ls:+8.1f} -> 3-Way Interaction = ${i_full:+8.1f}")
    print()
    
    # Save processed analysis
    out_analysis_path = r"c:\Users\Sundareswaran\Kagriculture\scratch\causal_factorial_analyzed.json"
    with open(out_analysis_path, "w") as fp:
        json.dump({
            "summary_stats": summary_stats,
            "main_effects": {
                "delta_q3": delta_q3,
                "delta_shop": delta_shop,
                "delta_ls": delta_ls,
                "delta_q3_margin": delta_q3_m,
                "delta_shop_margin": delta_shop_m,
                "delta_ls_margin": delta_ls_m,
            },
            "interactions": {
                "i_q3_shop": i_q3_shop,
                "i_q3_ls": i_q3_ls,
                "i_shop_ls": i_shop_ls,
                "i_full": i_full
            }
        }, fp, indent=2)
    print(f"Analysis successfully written to {out_analysis_path}")

if __name__ == "__main__":
    analyze_results()
