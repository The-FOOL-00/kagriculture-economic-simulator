"""
V39 Catalog & Result Distribution Analyzer
Analyzes all cataloged live V35 episodes.
"""

import json
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

LIVE_DIR = os.path.join(os.path.dirname(__file__), "..", "scratch", "v39", "live")
JSONL_PATH = os.path.join(LIVE_DIR, "episodes.jsonl")

def analyze():
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        episodes = [json.loads(line) for line in f if line.strip()]
        
    print(f"Total episodes: {len(episodes)}")
    
    wins = [e for e in episodes if e["result"] == "WIN"]
    losses = [e for e in episodes if e["result"] == "LOSS"]
    ties = [e for e in episodes if e["result"] == "TIE"]
    
    print(f"Wins: {len(wins)} ({len(wins)/len(episodes)*100:.1f}%)")
    print(f"Losses: {len(losses)} ({len(losses)/len(episodes)*100:.1f}%)")
    print(f"Ties: {len(ties)} ({len(ties)/len(episodes)*100:.1f}%)")
    
    margins = [e["margin"] for e in episodes]
    win_margins = [e["margin"] for e in wins]
    loss_margins = [e["margin"] for e in losses] # negative
    
    print("\n--- WIN MARGIN DISTRIBUTION ---")
    if win_margins:
        print(f"Min: {np.min(win_margins):.1f}, Median: {np.median(win_margins):.1f}, Mean: {np.mean(win_margins):.1f}, Max: {np.max(win_margins):.1f}")
        # Thresholds: Narrow: < 10000, Medium: 10000 - 50000, Large: > 50000
        narrow_w = [w for w in wins if w["margin"] < 10000]
        med_w = [w for w in wins if 10000 <= w["margin"] <= 50000]
        large_w = [w for w in wins if w["margin"] > 50000]
        print(f"Narrow Win (<$10k): {len(narrow_w)} ({[w['episode_id'] for w in narrow_w]})")
        print(f"Medium Win ($10k-$50k): {len(med_w)}")
        print(f"Large Win (>$50k): {len(large_w)}")
        
    print("\n--- LOSS MARGIN DISTRIBUTION ---")
    if loss_margins:
        abs_losses = [abs(m) for m in loss_margins]
        print(f"Min Loss Deficit: ${np.min(abs_losses):.1f}, Median Deficit: ${np.median(abs_losses):.1f}, Mean Deficit: ${np.mean(abs_losses):.1f}, Max Deficit: ${np.max(abs_losses):.1f}")
        # Severity thresholds:
        # Narrow loss: deficit < $2,000
        # Medium loss: deficit $2,000 - $15,000
        # Severe loss: deficit > $15,000
        narrow_l = [l for l in losses if abs(l["margin"]) < 2000]
        med_l = [l for l in losses if 2000 <= abs(l["margin"]) <= 15000]
        sev_l = [l for l in losses if abs(l["margin"]) > 15000]
        print(f"Narrow Loss (<$2k deficit): {len(narrow_l)} ({[(l['episode_id'], l['margin']) for l in narrow_l]})")
        print(f"Medium Loss ($2k-$15k deficit): {len(med_l)} ({[(l['episode_id'], l['margin']) for l in med_l]})")
        print(f"Severe Loss (>$15k deficit): {len(sev_l)} ({[(l['episode_id'], l['margin']) for l in sev_l]})")
        
    print("\n--- OPPONENT SUMMARY ---")
    opp_counts = {}
    for e in episodes:
        opp = e["opponent_name"]
        if opp not in opp_counts:
            opp_counts[opp] = {"total": 0, "WIN": 0, "LOSS": 0, "TIE": 0, "margins": []}
        opp_counts[opp]["total"] += 1
        opp_counts[opp][e["result"]] += 1
        opp_counts[opp]["margins"].append(e["margin"])
        
    for opp, stats in sorted(opp_counts.items(), key=lambda x: x[1]["total"], reverse=True):
        print(f"Opponent '{opp}': Total {stats['total']} | W: {stats['WIN']}, L: {stats['LOSS']}, T: {stats['TIE']} | Mean Margin: ${np.mean(stats['margins']):.1f}")
        
    print("\n--- SEAT BREAKDOWN ---")
    seat0 = [e for e in episodes if e["seat"] == 0]
    seat1 = [e for e in episodes if e["seat"] == 1]
    s0_wins = sum(1 for e in seat0 if e["result"] == "WIN")
    s1_wins = sum(1 for e in seat1 if e["result"] == "WIN")
    print(f"Seat 0: {len(seat0)} games, {s0_wins} Wins ({s0_wins/len(seat0)*100:.1f}%), Mean Margin: ${np.mean([e['margin'] for e in seat0]):.1f}")
    print(f"Seat 1: {len(seat1)} games, {s1_wins} Wins ({s1_wins/len(seat1)*100:.1f}%), Mean Margin: ${np.mean([e['margin'] for e in seat1]):.1f}")

if __name__ == "__main__":
    analyze()
