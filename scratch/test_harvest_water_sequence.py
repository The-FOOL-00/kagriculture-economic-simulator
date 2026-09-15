"""
Test Harvest + Water on same tile to prevent weed decay.
"""
import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim

g = kagsim.Game(50003)
# Plant a tomato on (0, 0) on day 0
# Give money and seed
# Water daily
# On day 8 (maturity), harvest on hour 8, water on hour 9
# Verify that tomato is harvested AND continues growing to day 9!
print("Testing Harvest + Water sequential execution on same tile...")

# Run to see engine behavior
for day in range(12):
    # hour 0: plant on day 0
    for hour in range(24):
        step = day * 24 + hour
        a0 = {"farmer": ["PASS"], "hands": [], "market": []}
        if step == 0:
            a0["market"] = [["BUY_SEED", "TOMATO", 1]]
        elif step == 1:
            a0["farmer"] = ["NORTH"] # move
        elif step == 2:
            a0["farmer"] = ["WEST"]
        # ...
