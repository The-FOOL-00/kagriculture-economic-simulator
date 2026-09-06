import sys
import os
sys.path.insert(0, os.path.abspath("."))
import candidates.slot2_aethel_refined_v2 as v2

print("V2 Actions on Day 1 (Steps 24-47):")
for s in range(24, 48):
    act = v2._TRACE[s]
    farmer = act.get("farmer", [])
    hands = act.get("hands", [])
    market = act.get("market", [])
    print(f"Step {s:2d}: Farmer: {farmer} | Hands ({len(hands)}): {hands} | Market: {market}")
