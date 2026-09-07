import sys, os
sys.path.insert(0, os.path.abspath("."))
import candidates.slot2_aethel_refined_v2 as v2

trace = v2._TRACE
for s in range(25):
    print(f"Step {s:2d}: Farmer={trace[s].get('farmer')} | Hands={trace[s].get('hands')} | Market={trace[s].get('market')}")
