import sys
import os
sys.path.insert(0, os.path.abspath("."))
import candidates.slot2_aethel_refined_v2 as v2

print("Inspecting all PLANT MELON and HARVEST in V2's plan:")
for s, act in enumerate(v2._TRACE):
    farmer = act.get("farmer", [])
    hands = act.get("hands", [])
    all_acts = [farmer] + hands
    has_melon_plant = any(len(a) >= 2 and a[0] == "PLANT" and a[1] == "MELON" for a in all_acts)
    has_harvest = any("HARVEST" in a for a in all_acts)
    if has_melon_plant or (has_harvest and s in range(250, 275)):
        print(f"Step {s:3d} (Day {s//24:2d}, Hr {s%24:2d}): Farmer: {farmer} | Hands: {hands}")
