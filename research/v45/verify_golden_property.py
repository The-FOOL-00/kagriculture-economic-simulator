# SPDX-License-Identifier: MIT
"""V45 Golden Property Verification Test.

Evaluates candidates/v45_adversarial_market/main.py vs candidates/v44_economic_portfolio/main.py
across 15 complete games (10,800 total turns) to guarantee 100% bit-for-bit action equality.
"""

from __future__ import annotations
import copy
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v45.governance import assert_seed_safe, assert_protected_artifacts
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v45_adversarial_market.main import V45CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

DEV_SEEDS = [249635, 249636, 249637, 249645, 249646, 249655, 249656, 249685]
OPPONENTS = ["E8_DMITRII", "E2_A7"]


def verify_golden_property():
    print("=" * 80)
    print("V45 GOLDEN PROPERTY VERIFICATION (10,000+ TURNS AUDIT)")
    print("=" * 80)
    assert_protected_artifacts()
    for s in DEV_SEEDS:
        assert_seed_safe(s)

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    total_turns = 0
    discrepancies = 0
    games_tested = 0
    t0 = time.perf_counter()

    for seed in DEV_SEEDS:
        for opp_id in OPPONENTS:
            if games_tested >= 15:
                break
            games_tested += 1
            sim = FastKagricultureSim(seed=seed)
            v45 = V45CandidateController(enable_experimental_market=False)
            v44 = V44CandidateController()
            opp = copy.deepcopy(opp_masters[opp_id])

            obs0, obs1 = sim.reset(seed=seed)

            while not sim.done:
                total_turns += 1
                act45 = v45.act(obs0)
                act44 = v44.act(obs0)

                if act45 != act44:
                    discrepancies += 1
                    print(f"DISCREPANCY at Seed {seed}, Step {obs0.get('step', 0)}:")
                    print("  V45:", act45)
                    print("  V44:", act44)

                act_opp = opp(obs1)
                [obs0, obs1], _, _, _ = sim.step([act45, act_opp])

    dur = time.perf_counter() - t0
    print(f"\nVerification Results:")
    print(f"Total Games Tested: {games_tested}")
    print(f"Total Turns Evaluated: {total_turns}")
    print(f"Total Discrepancies: {discrepancies}")
    print(f"Execution Duration: {dur:.1f}s")

    if discrepancies == 0 and total_turns >= 10000:
        print(">> PASS: Golden Property 100% Verified! V45 == V44 across all turns.")
        return True
    else:
        print(">> FAIL: Discrepancy detected or insufficient turn volume.")
        return False


if __name__ == "__main__":
    verify_golden_property()
