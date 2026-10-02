import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import candidates.v48_challenger.main as v48_mod

chassis = v48_mod._IMPL.chassis

print("--- Route 2 Market Actions in steps 690..719 ---")
for t in range(690, 719):
    act = chassis.routes[2][t]
    mkt = act.get("market", [])
    if mkt:
        print(f"Step {t}: {mkt}")
