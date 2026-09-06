import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
from scratch.v2_jit_melon_experiment import CANONICAL_JIT_TRACE

for s in range(25):
    act = CANONICAL_JIT_TRACE[s]
    farmer = act.get("farmer", [])
    hands = act.get("hands", [])
    market = act.get("market", [])
    print(f"Step {s:2d}: Farmer: {farmer} | Hands ({len(hands)}): {hands[:2]} | Market: {market}")
