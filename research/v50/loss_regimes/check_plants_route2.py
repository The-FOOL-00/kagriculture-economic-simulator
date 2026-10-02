import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import candidates.v48_challenger.main as v48_mod

chassis = v48_mod._IMPL.chassis

print("--- Route 2 Unit PLANT Actions post-step 648 ---")
for t in range(648, 719):
    act = chassis.routes[2][t]
    units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
    plants = [c for c in units if len(c) > 0 and c[0] == "PLANT"]
    if plants:
        print(f"Step {t} (Day {t//24} h {t%24}): {plants}")
