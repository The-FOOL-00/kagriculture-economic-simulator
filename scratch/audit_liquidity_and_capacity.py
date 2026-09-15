"""
scratch/audit_liquidity_and_capacity.py
=======================================
Analyzes:
1. Horizon effect: optimal wheat-vs-livestock decisions across Days 15, 17, 19, 21, 23, 25, 27, and terminal window.
2. Liquidity effect: cash flow timing vs ultimate commodity value.
3. Physical capacity effect: shed/pasture capacity constraints, shearing/milking bottlenecks.
4. Market endogeneity: agent sales price impact.
5. Regime classification: predictive accuracy of public state before decision.
Outputs:
- research/midlate_liquidity_capacity_analysis.json
"""

import os
import sys
import json
import numpy as np
from collections import defaultdict

def main():
    print("Loading telemetry from research/midlate_accounting_telemetry.json...")
    if not os.path.exists("research/midlate_accounting_telemetry.json"):
        print("Telemetry not ready yet. Please ensure audit_midlate_loss_regime.py completes.")
        return

    with open("research/midlate_accounting_telemetry.json") as f:
        matches = json.load(f)

    print(f"Loaded {len(matches)} telemetry matches.")

    # 1. Horizon Effect Analysis
    # Analyze checkpoint differences at steps 336 (Day 14), 384 (Day 16), 432 (Day 18), 480 (Day 20), 528 (Day 22), 576 (Day 24), 624 (Day 26)
    horizon_metrics = defaultdict(lambda: {"v54_cash": [], "v66_cash": [], "v54_wheat_sold": [], "v66_wheat_sold": [], "wheat_price": [], "wool_price": [], "milk_price": []})

    for m in matches:
        cps = m.get("checkpoints", {})
        for s_str, data in cps.items():
            s = int(s_str)
            horizon_metrics[s]["v54_cash"].append(data["v54"]["cash"])
            horizon_metrics[s]["v66_cash"].append(data["v66"]["cash"])
            horizon_metrics[s]["v54_wheat_sold"].append(data["v54"]["wheat_sold"])
            horizon_metrics[s]["v66_wheat_sold"].append(data["v66"]["wheat_sold"])
            horizon_metrics[s]["wheat_price"].append(data["prices"]["wheat"])
            horizon_metrics[s]["wool_price"].append(data["prices"]["wool"])
            horizon_metrics[s]["milk_price"].append(data["prices"]["milk"])

    horizon_summary = {}
    for s, d in sorted(horizon_metrics.items()):
        horizon_summary[s] = {
            "day": s // 24,
            "avg_v54_cash": float(np.mean(d["v54_cash"])),
            "avg_v66_cash": float(np.mean(d["v66_cash"])),
            "cash_gap_v66_lead": float(np.mean(d["v66_cash"]) - np.mean(d["v54_cash"])),
            "avg_v54_wheat_sold": float(np.mean(d["v54_wheat_sold"])),
            "avg_v66_wheat_sold": float(np.mean(d["v66_wheat_sold"])),
            "wheat_sold_lead": float(np.mean(d["v66_wheat_sold"]) - np.mean(d["v54_wheat_sold"])),
            "avg_wheat_price": float(np.mean(d["wheat_price"])),
            "avg_wool_price": float(np.mean(d["wool_price"])),
            "avg_milk_price": float(np.mean(d["milk_price"])),
        }

    # 2. Liquidity Effect
    # Check if cash flow at Day 18-22 bottlenecks worker hiring or fertilizer
    loss_matches = [m for m in matches if m["v66_reward"] - m["v54_reward"] >= 2500]
    win_matches = [m for m in matches if m["v54_reward"] - m["v66_reward"] >= 2500]

    def extract_liquidity(match_list):
        if not match_list: return {}
        cash_gap_mid = []
        wheat_rev_gap = []
        for m in match_list:
            cp480 = m.get("checkpoints", {}).get("480", {})
            if cp480:
                cash_gap_mid.append(cp480["v66"]["cash"] - cp480["v54"]["cash"])
                wheat_rev_gap.append(cp480["v66"]["wheat_revenue"] - cp480["v54"]["wheat_revenue"])
        return {
            "avg_midgame_cash_gap": float(np.mean(cash_gap_mid)) if cash_gap_mid else 0.0,
            "avg_midgame_wheat_revenue_gap": float(np.mean(wheat_rev_gap)) if wheat_rev_gap else 0.0,
        }

    liquidity_analysis = {
        "loss_seeds": extract_liquidity(loss_matches),
        "win_seeds": extract_liquidity(win_matches),
    }

    # 3. Physical Capacity Effect
    # Track cows, sheep, feed consumed, milk/wool produced
    capacity_analysis = {}
    for group_name, m_list in [("Loss Matches", loss_matches), ("Win Matches", win_matches)]:
        if not m_list: continue
        v54_cows = [m["cumulative"]["v54"]["cows_bought"] for m in m_list]
        v66_cows = [m["cumulative"]["v66"]["cows_bought"] for m in m_list]
        v54_sheep = [m["cumulative"]["v54"]["sheep_bought"] for m in m_list]
        v66_sheep = [m["cumulative"]["v66"]["sheep_bought"] for m in m_list]
        v54_feed = [m["cumulative"]["v54"]["wheat_consumed"] for m in m_list]
        v66_feed = [m["cumulative"]["v66"]["wheat_consumed"] for m in m_list]
        v54_wool = [m["cumulative"]["v54"]["wool_produced"] for m in m_list]
        v66_wool = [m["cumulative"]["v66"]["wool_produced"] for m in m_list]
        v54_milk = [m["cumulative"]["v54"]["milk_produced"] for m in m_list]
        v66_milk = [m["cumulative"]["v66"]["milk_produced"] for m in m_list]

        capacity_analysis[group_name] = {
            "v54_avg_cows": float(np.mean(v54_cows)),
            "v66_avg_cows": float(np.mean(v66_cows)),
            "v54_avg_sheep": float(np.mean(v54_sheep)),
            "v66_avg_sheep": float(np.mean(v66_sheep)),
            "v54_avg_feed_consumed": float(np.mean(v54_feed)),
            "v66_avg_feed_consumed": float(np.mean(v66_feed)),
            "v54_avg_wool": float(np.mean(v54_wool)),
            "v66_avg_wool": float(np.mean(v66_wool)),
            "v54_avg_milk": float(np.mean(v54_milk)),
            "v66_avg_milk": float(np.mean(v66_milk)),
        }

    # 4. Regime Classification Analysis
    # Regime A: Direct wheat liquidation superior (loss matches where wheat was sold at high price)
    # Regime B: Livestock conversion superior (win matches where wool/milk produced large margin)
    # Regime C: Indifferent (close matches)
    regime_counts = {
        "Regime A (Wheat Superior)": len(loss_matches),
        "Regime B (Livestock Superior)": len(win_matches),
        "Regime C (Indifferent)": len(matches) - len(loss_matches) - len(win_matches),
    }

    # Evaluate simple public-state price predictor:
    # Predict Regime A if average wheat price in Days 15-22 >= 20.0 and wool price < 50.0
    true_labels = [] # 1 for Regime A, 0 for Regime B
    pred_labels = []

    for m in loss_matches + win_matches:
        is_regime_a = (m in loss_matches)
        true_labels.append(1 if is_regime_a else 0)
        # Check prices at Step 480
        cp = m.get("checkpoints", {}).get("480", {})
        if cp:
            pw = cp["prices"]["wheat"]
            pwool = cp["prices"]["wool"]
            pred_a = (pw >= 20.0 and pwool < 50.0)
            pred_labels.append(1 if pred_a else 0)
        else:
            pred_labels.append(0)

    true_arr = np.array(true_labels)
    pred_arr = np.array(pred_labels)
    acc = float(np.mean(true_arr == pred_arr)) if len(true_arr) > 0 else 0.0
    tp = int(np.sum((true_arr == 1) & (pred_arr == 1)))
    fp = int(np.sum((true_arr == 0) & (pred_arr == 1)))
    fn = int(np.sum((true_arr == 1) & (pred_arr == 0)))
    tn = int(np.sum((true_arr == 0) & (pred_arr == 0)))

    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    classification_metrics = {
        "regime_counts": regime_counts,
        "sample_size": len(true_labels),
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
    }

    full_output = {
        "horizon_effect": horizon_summary,
        "liquidity_effect": liquidity_analysis,
        "physical_capacity_effect": capacity_analysis,
        "regime_classification": classification_metrics,
    }

    print("Writing research/midlate_liquidity_capacity_analysis.json...")
    with open("research/midlate_liquidity_capacity_analysis.json", "w") as f:
        json.dump(full_output, f, indent=2)

    print("Liquidity and capacity analysis complete!")

if __name__ == "__main__":
    main()
