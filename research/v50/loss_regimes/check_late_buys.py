import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import candidates.v48_challenger.main as v48_mod

chassis = v48_mod._IMPL.chassis

print("--- Route 0 Market Actions in steps 600..648 ---")
for t in range(600, 648):
    act = chassis.routes[0][t]
    mkt = act.get("market", [])
    buys = [o for o in mkt if o and o[0] in ("BUY_PRODUCT", "BUY_SEED")]
    if buys:
        print(f"Step {t}: {buys}")

print("\n--- Route 2 Market Actions in steps 648..719 ---")
for t in range(648, 719):
    act = chassis.routes[2][t]
    mkt = act.get("market", [])
    buys = [o for o in mkt if o and o[0] in ("BUY_PRODUCT", "BUY_SEED")]
    if buys:
        print(f"Step {t}: {buys}")
