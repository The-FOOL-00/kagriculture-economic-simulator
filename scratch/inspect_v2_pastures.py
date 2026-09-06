import sys
import os
sys.path.insert(0, os.path.abspath("."))
import candidates.slot2_aethel_refined_v2 as v2

print("Inspecting all BUILD_PASTURE actions in V2's plan:")
for s, act in enumerate(v2._TRACE):
    farmer = act.get("farmer", [])
    hands = act.get("hands", [])
    if "BUILD_PASTURE" in farmer or any("BUILD_PASTURE" in h for h in hands):
        print(f"Step {s:3d} (Day {s//24:2d}, Hr {s%24:2d}): Farmer: {farmer} | Hands: {hands}")
