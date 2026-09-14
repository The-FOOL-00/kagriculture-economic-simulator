# SPDX-License-Identifier: MIT
"""EXP-DEV-006 treatment identity probe (pre-execution, zero game simulation).

Proves on SYNTHETIC observations (no seeds, no simulator):
  1. DEV-006 valuation outputs are identical to DEV-005 for all 6 plans at all 4 checkpoints.
  2. DEV-006 checkpoint decisions are identical to DEV-005 at steps 72/144/216 (remaining >= 500).
  3. The ONLY divergence is at step 288 (remaining 432 < 500), where an otherwise-eligible
     specialization becomes REJECT_HORIZON under DEV-006 while DEV-005 specializes.

Exit 0 = one-factor identity confirmed. Any other outcome = STOP.
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from dev_006_horizon_guard_scheduler import (
    Dev006HorizonGuardScheduler,
    HORIZON_GUARD_THRESHOLD,
)

PLANS = ("BASELINE_BACKBONE", "YARN_SPECIALIZED", "BAKERY_SPECIALIZED",
         "PET_SPECIALIZED", "SMOOTHIE_SPECIALIZED", "PIZZA_ADAPTIVE")
SHOPS = ["YARN_STORE", "BAKERY", "PET_CAFE", "SMOOTHIE_SHOP"]
PRICES = {"WHEAT": 25.0, "CARROT": 35.0, "TOMATO": 60.0, "STRAWBERRY": 120.0,
          "MELON": 250.0, "WOOL": 400.0, "MILK": 160.0, "EGG": 40.0}


def mkobs(step):
    return {"player": 0, "step": step,
            "farms": [{"money": 50000.0}],
            "town": {"unlocked_shops": list(SHOPS)},
            "market": {"prices": dict(PRICES)}}


def main():
    assert HORIZON_GUARD_THRESHOLD == 500, "H must be exactly 500"
    failures = []
    for step in (72, 144, 216, 288):
        a = Dev005ConfirmedShopScheduler(seat=0, seed=0)
        b = Dev006HorizonGuardScheduler(seat=0, seed=0)
        obs = mkobs(step)
        for plan in PLANS:
            va = a.evaluate_plan_feasibility_and_value(plan, obs, step, SHOPS, PRICES, 50000.0)
            vb = b.evaluate_plan_feasibility_and_value(plan, obs, step, SHOPS, PRICES, 50000.0)
            if va != vb:
                failures.append(f"step {step} plan {plan}: valuation differs")
        a.evaluate_checkpoints(obs, step)
        b.evaluate_checkpoints(obs, step)
        da, db = a.decision_events[-1], b.decision_events[-1]
        ka = {k: v for k, v in da.items() if k not in ("remaining_horizon", "horizon_satisfied")}
        kb = {k: v for k, v in db.items() if k not in ("remaining_horizon", "horizon_satisfied")}
        remaining = 720 - step
        if remaining >= 500:
            if ka != kb:
                failures.append(f"step {step}: decisions differ above guard: {da['decision']} vs {db['decision']}")
            print(f"step={step} remain={remaining}: IDENTICAL ({da['decision']}/{da['best_candidate_plan']}/{da['expected_incremental_value']})")
        else:
            ok = (da["decision"] == "SPECIALIZE_CONFIRMED"
                  and db["decision"] == "REJECT_HORIZON"
                  and da["best_candidate_plan"] == db["best_candidate_plan"]
                  and da["expected_incremental_value"] == db["expected_incremental_value"])
            print(f"step={step} remain={remaining}: DEV005={da['decision']} DEV006={db['decision']} "
                  f"(candidate {db['best_candidate_plan']} value {db['expected_incremental_value']})")
            if not ok:
                failures.append(f"step {step}: expected SPECIALIZE vs REJECT_HORIZON divergence")
    if failures:
        print("IDENTITY PROBE FAILED:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("IDENTITY PROBE: PASS — one-factor guard confirmed, all else identical.")


if __name__ == "__main__":
    main()
