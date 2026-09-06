"""
Simulation test:
Construct a Day-0 state where:
1. Pastures are at V2's exact coordinates: (2,4), (3,4), (4,3), (4,4)
2. Animals: 2 Cows, 2 Sheep placed in pastures
3. 12 Melons planted on tiles: (0,0)..(0,4), (1,0)..(1,4), (2,0)..(2,1)
4. 7 Wheat planted on tiles: (2,2)..(2,3), (3,0)..(3,2), (4,0)..(4,1)
5. All 19 crops watered on Day 0
6. Shed has >= 5 wheat for Day 1 feeding
7. At Step 24, V2 takes over!

Let's test how V2 scores with this Day 0 state!
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import copy
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

# Let's inspect V2's step 0-23 actions to see how V2 moves on Day 0
# and adapt them to plant 12 melons and 7 wheat and build pastures at (2,4),(3,4),(4,3),(4,4)

v2_trace = v2._TRACE

print("V2 Day 0 steps inspection...")
for s in range(24):
    act = v2_trace[s]
    print(f"Step {s:2d}: Farmer={act.get('farmer')} | Hands={act.get('hands')} | Mkt={act.get('market')}")
