"""
Deep forensic analysis of why External Wheat and Cow Scaling degrade in closed loop play.
Inspects cash drain, market price escalation, feed starvation, and opportunity cost.
"""

import json
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("scratch/feed_arbitrage_factorial_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

# Analyze differences between Base V2 and Treatment H against each opponent
print("=" * 100)
print("DEEP LOSS FORENSICS: BASE V2 VS TREATMENT H (ALL THREE)")
print("=" * 100)

for opp in ["aethel_v2_closed", "live_flooder_v1", "replay_crop_dusta", "replay_kawatta_taido", "replay_whyme_labs"]:
    base_rows = [r for r in results if r["treatment"] == "A_BASE_V2" and r["opponent"] == opp]
    h_rows = [r for r in results if r["treatment"] == "H_ALL_THREE_12C" and r["opponent"] == opp]
    
    base_score = np.mean([r["reward_us"] for r in base_rows])
    h_score = np.mean([r["reward_us"] for r in h_rows])
    base_margin = np.mean([r["margin"] for r in base_rows])
    h_margin = np.mean([r["margin"] for r in h_rows])
    base_starv = sum(r["starvation_events"] for r in base_rows)
    h_starv = sum(r["starvation_events"] for r in h_rows)
    base_wht = np.mean([r["wheat_bought"] for r in base_rows])
    h_wht = np.mean([r["wheat_bought"] for r in h_rows])
    base_cows = np.mean([r["final_cows"] for r in base_rows])
    h_cows = np.mean([r["final_cows"] for r in h_rows])
    
    print(f"\nOpponent: {opp}")
    print(f"  Base V2 Score: ${base_score:9.1f} (Margin: ${base_margin:+9.1f}) | Wheat: {base_wht:.1f} | Cows: {base_cows:.1f} | Starvations: {base_starv}")
    print(f"  Treat H Score: ${h_score:9.1f} (Margin: ${h_margin:+9.1f}) | Wheat: {h_wht:.1f} | Cows: {h_cows:.1f} | Starvations: {h_starv}")
    print(f"  Delta:         ${h_score - base_score:+9.1f} (Margin Delta: ${h_margin - base_margin:+9.1f})")

print("\n" + "=" * 100)
