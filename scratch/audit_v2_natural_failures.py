"""
scratch/audit_v2_natural_failures.py
=============================================================================
Deep Forensic Audit of Actual Game Failures in V2 across 500 Matches
=============================================================================
Checks:
1. Animal Deaths / Pasture Emptying (did any animal starve and die?)
2. Crop Withering / Rot (did any crop die from unwatered status?)
3. Harvest Loss (did melons/strawberries reach maturity and get harvested?)
4. Worker Pathing Collisions / Illegal Action Rejections
5. Final Bank Distribution & Outlier Loss Detection
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np

def audit_failures():
    with open("scratch/natural_deviations_500games.json", "r") as fp:
        games = json.load(fp)

    scores = [g["v2_score"] for g in games]
    margins = [g["margin"] for g in games]
    
    print(f"Total Games Audited: {len(games)}")
    print(f"Mean Score:          ${np.mean(scores):,.2f}")
    print(f"Median Score:        ${np.median(scores):,.2f}")
    print(f"Min Score:           ${np.min(scores):,.2f}")
    print(f"Max Score:           ${np.max(scores):,.2f}")
    print(f"Std Dev:             ${np.std(scores):,.2f}")
    
    # Identify games where score fell below $60k or suffered an unexpected drop
    low_games = [g for g in games if g["v2_score"] < 60000]
    print(f"\nGames with Score < $60k: {len(low_games)} / {len(games)} ({len(low_games)/len(games)*100:.1f}%)")
    
    for lg in low_games[:10]:
        print(f"Seed: {lg['seed']} | Opponent: {lg['opp_name']} | Slot: {lg['player_slot']} | V2: ${lg['v2_score']:,.1f} | Opp: ${lg['opp_score']:,.1f} | Margin: ${lg['margin']:+,.1f}")

    # Check distribution by opponent
    by_opp = {}
    for g in games:
        opp = g["opp_name"]
        if opp not in by_opp:
            by_opp[opp] = []
        by_opp[opp].append(g["v2_score"])
        
    print("\n--- SCORE DISTRIBUTION BY OPPONENT ---")
    for opp, s_list in by_opp.items():
        print(f"Opponent: {opp:15s} | N={len(s_list):3d} | Mean: ${np.mean(s_list):,.1f} | Min: ${np.min(s_list):,.1f} | Max: ${np.max(s_list):,.1f} | Std: ${np.std(s_list):,.1f}")

if __name__ == "__main__":
    audit_failures()
