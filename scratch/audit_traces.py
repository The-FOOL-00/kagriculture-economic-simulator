import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import CANONICAL_JIT_TRACE

v2_trace = v2._TRACE

print(f"V2 trace length: {len(v2_trace)}")
print(f"H trace length: {len(CANONICAL_JIT_TRACE)}")

diff_steps = []
market_diff = []
hands_diff = []
farmer_diff = []

for s in range(min(len(v2_trace), len(CANONICAL_JIT_TRACE))):
    v_act = v2_trace[s]
    h_act = CANONICAL_JIT_TRACE[s]
    d = False
    if v_act.get("farmer") != h_act.get("farmer"):
        farmer_diff.append(s)
        d = True
    if v_act.get("hands") != h_act.get("hands"):
        hands_diff.append(s)
        d = True
    if v_act.get("market") != h_act.get("market"):
        market_diff.append(s)
        d = True
    if d:
        diff_steps.append(s)

print(f"Total steps differing in any field: {len(diff_steps)}")
print(f"Farmer differing steps: {len(farmer_diff)}, first 10: {farmer_diff[:10]}")
print(f"Hands differing steps: {len(hands_diff)}, first 10: {hands_diff[:10]}")
print(f"Market differing steps: {len(market_diff)}, first 10: {market_diff[:10]}")

if diff_steps:
    print(f"Earliest differing step: {diff_steps[0]}")
    print(f"Latest differing step: {diff_steps[-1]}")
    
# Check after step 288, 336, 500, etc.
diffs_after_288 = [s for s in diff_steps if s >= 288]
print(f"Differing steps after step 288: {len(diffs_after_288)}")
diffs_after_500 = [s for s in diff_steps if s >= 500]
print(f"Differing steps after step 500: {len(diffs_after_500)}")
diffs_after_700 = [s for s in diff_steps if s >= 700]
print(f"Differing steps after step 700: {len(diffs_after_700)}")
