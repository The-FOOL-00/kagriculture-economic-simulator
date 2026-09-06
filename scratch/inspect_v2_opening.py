import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import candidates.slot2_aethel_refined_v2 as v2

for s in range(25):
    act = v2._TRACE[s]
    farmer = act.get("farmer", [])
    hands = act.get("hands", [])
    market = act.get("market", [])
    print(f"Step {s:2d}: Farmer: {farmer} | Hands ({len(hands)}): {hands[:2]} | Market: {market}")
