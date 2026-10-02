import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import candidates.v48_challenger.main as v48_mod

chassis = v48_mod._IMPL.chassis

for r_id in (0, 2):
    print(f"=== Route {r_id} Unit FERTILIZE Actions post-step 500 ===")
    for t in range(500, 719):
        act = chassis.routes[r_id][t]
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        ferts = [c for c in units if len(c) > 0 and c[0] == "FERTILIZE"]
        if ferts:
            print(f"Step {t} (Day {t//24} h {t%24}): {ferts}")
