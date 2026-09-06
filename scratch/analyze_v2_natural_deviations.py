"""
scratch/analyze_v2_natural_deviations.py
=============================================================================
Phase 2, 3, 4, 5: Taxonomy Analysis, Economic Valuation, Root Causes, Invariants
=============================================================================
Parses scratch/natural_deviations_500games.json, computes comprehensive
frequency and loss statistics, groups by D1-D13 taxonomy, analyzes root causes,
identifies V2 hard invariants, and evaluates Expected Value (EV).
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import numpy as np
from collections import defaultdict

def analyze_mined_telemetry(json_path="scratch/natural_deviations_500games.json"):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist.")
        return None

    with open(json_path, "r") as fp:
        games = json.load(fp)

    total_games = len(games)
    print(f"\n=============================================================================")
    print(f"V2 NATURAL DEVIATION AUDIT: {total_games} GAMES ANALYZED")
    print(f"=============================================================================\n")

    # Matchup breakdowns
    matchup_stats = defaultdict(lambda: {"count": 0, "scores": [], "margins": [], "wins": 0, "deviations": []})
    for g in games:
        m_name = g["opp_name"]
        matchup_stats[m_name]["count"] += 1
        matchup_stats[m_name]["scores"].append(g["v2_score"])
        matchup_stats[m_name]["margins"].append(g["margin"])
        if g["win"] > 0:
            matchup_stats[m_name]["wins"] += 1
        matchup_stats[m_name]["deviations"].extend(g["deviations"])

    print("--- MATCHUP SUMMARY ---")
    for m_name, s in matchup_stats.items():
        avg_score = np.mean(s["scores"])
        avg_margin = np.mean(s["margins"])
        win_rate = s["wins"] / s["count"] * 100
        dev_count = len(s["deviations"])
        print(f"Opponent: {m_name:15s} | Matches: {s['count']:3d} | Win Rate: {win_rate:5.1f}% | Avg Score: ${avg_score:,.1f} | Avg Margin: ${avg_margin:+,.1f} | Deviations: {dev_count}")

    # Deviation taxonomy breakdown
    taxonomy = defaultdict(lambda: {"count": 0, "affected_games": set(), "first_steps": [], "details": []})
    for g_idx, g in enumerate(games):
        for d in g.get("deviations", []):
            d_type = d.get("type", "D13")
            d_cat = d.get("category", "other")
            key = f"{d_type}:{d_cat}"
            taxonomy[key]["count"] += 1
            taxonomy[key]["affected_games"].add(g_idx)
            taxonomy[key]["first_steps"].append(d.get("step", 0))
            if len(taxonomy[key]["details"]) < 5:
                taxonomy[key]["details"].append(d.get("detail", ""))

    print("\n--- DEVIATION TAXONOMY BREAKDOWN (D1-D13) ---")
    print(f"{'Code & Category':35s} | {'Total Events':12s} | {'Games Affected':14s} | {'Game Freq %':11s} | {'First Step':10s}")
    print("-" * 95)
    
    ranked_deviations = []
    for key, data in sorted(taxonomy.items(), key=lambda x: len(x[1]["affected_games"]), reverse=True):
        games_aff = len(data["affected_games"])
        freq_pct = (games_aff / total_games) * 100
        min_step = min(data["first_steps"]) if data["first_steps"] else 0
        median_step = np.median(data["first_steps"]) if data["first_steps"] else 0
        print(f"{key:35s} | {data['count']:12d} | {games_aff:14d} | {freq_pct:10.1f}% | Step {int(median_step):3d}")
        
        ranked_deviations.append({
            "key": key,
            "total_events": data["count"],
            "games_affected": games_aff,
            "game_frequency_pct": freq_pct,
            "median_step": float(median_step),
            "samples": data["details"]
        })

    # Economic Loss Estimation
    print("\n--- ECONOMIC LOSS & EXPECTED VALUE (EV) ANALYSIS ---")
    # Estimate loss per event based on counterfactual game scores
    # Compare games with deviations vs clean games in same matchup
    clean_scores = [g["v2_score"] for g in games if g["deviation_count"] == 0]
    dev_scores = [g["v2_score"] for g in games if g["deviation_count"] > 0]
    
    clean_mean = np.mean(clean_scores) if clean_scores else 0
    dev_mean = np.mean(dev_scores) if dev_scores else 0
    diff = clean_mean - dev_mean
    
    print(f"Clean Games Mean Score (N={len(clean_scores)}): ${clean_mean:,.2f}")
    print(f"Dev Games Mean Score (N={len(dev_scores)}):   ${dev_mean:,.2f}")
    print(f"Observed Aggregate Score Delta:              ${diff:,.2f}")

    # Save summary report dictionary
    summary_report = {
        "total_games": total_games,
        "clean_games_count": len(clean_scores),
        "clean_games_mean_score": float(clean_mean),
        "dev_games_count": len(dev_scores),
        "dev_games_mean_score": float(dev_mean),
        "observed_aggregate_delta": float(diff),
        "matchup_breakdown": {
            m_name: {
                "matches": s["count"],
                "win_rate": float(s["wins"] / s["count"] * 100),
                "avg_score": float(np.mean(s["scores"])),
                "avg_margin": float(np.mean(s["margins"])),
                "total_deviations": len(s["deviations"])
            }
            for m_name, s in matchup_stats.items()
        },
        "taxonomy": ranked_deviations
    }

    out_path = "scratch/v2_deviation_analysis_summary.json"
    with open(out_path, "w") as fp:
        json.dump(summary_report, fp, indent=2)
    print(f"\nSaved analysis summary to {out_path}")

    return summary_report

if __name__ == "__main__":
    analyze_mined_telemetry()
