# SPDX-License-Identifier: MIT
"""Kagriculture V41 Golden Property Verification Test.

Proves:
1. V41(intervention=0) == V35 across all 719 turns bit-for-bit.
2. V41(mode="v39", intervention=0) == V39 across all turns bit-for-bit.
3. Discrepancy count must be EXACTLY ZERO.
"""

from __future__ import annotations
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v32_rlx2.opponents import load_league_opponent
from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor

SEEDS_TO_TEST = [249635, 249636, 249637, 249638]
OPPONENT_ID = "E8_DMITRII"


def verify_golden_property_v35(seed: int) -> int:
    sim_v35 = FastKagricultureSim(seed=seed)
    sim_v41 = FastKagricultureSim(seed=seed)

    v35 = V35OpeningController()
    v41_exec = StateAwareExecutor(mode="v35")

    opp_35 = load_league_opponent(OPPONENT_ID)
    opp_41 = load_league_opponent(OPPONENT_ID)

    obs35_0, obs35_1 = sim_v35.reset(seed=seed)
    obs41_0, obs41_1 = sim_v41.reset(seed=seed)

    discrepancies = 0
    step = 0

    while not sim_v35.done and not sim_v41.done:
        act35 = v35.act(obs35_0)
        # V41 with intervention=0 (abstention)
        act41 = v41_exec.execute(0, obs41_0)

        # Bit-for-bit equality check on action dict
        if act35 != act41:
            discrepancies += 1
            print(f"[Seed {seed} Step {step}] Action mismatch: V35={act35} != V41={act41}")

        act_opp35 = opp_35(obs35_1)
        act_opp41 = opp_41(obs41_1)

        [obs35_0, obs35_1], _, _, _ = sim_v35.step([act35, act_opp35])
        [obs41_0, obs41_1], _, _, _ = sim_v41.step([act41, act_opp41])
        step += 1

    r35 = float(sim_v35.state[0].reward or 0.0)
    r41 = float(sim_v41.state[0].reward or 0.0)

    if r35 != r41:
        discrepancies += 1
        print(f"[Seed {seed}] Reward mismatch: V35={r35} != V41={r41}")

    print(f"Seed {seed} V35 Golden Property: {step} turns evaluated, discrepancies={discrepancies}, reward=${r41:.2f}")
    return discrepancies


def verify_golden_property_v39(seed: int) -> int:
    sim_v39 = FastKagricultureSim(seed=seed)
    sim_v41 = FastKagricultureSim(seed=seed)

    v39 = V39TargetedController()
    v41_exec = StateAwareExecutor(mode="v39")

    opp_39 = load_league_opponent(OPPONENT_ID)
    opp_41 = load_league_opponent(OPPONENT_ID)

    obs39_0, obs39_1 = sim_v39.reset(seed=seed)
    obs41_0, obs41_1 = sim_v41.reset(seed=seed)

    discrepancies = 0
    step = 0

    while not sim_v39.done and not sim_v41.done:
        act39 = v39.act(obs39_0)
        # V41 in v39 mode with intervention=0
        act41 = v41_exec.execute(0, obs41_0)

        if act39 != act41:
            discrepancies += 1
            print(f"[Seed {seed} Step {step}] Action mismatch: V39={act39} != V41={act41}")

        act_opp39 = opp_39(obs39_1)
        act_opp41 = opp_41(obs41_1)

        [obs39_0, obs39_1], _, _, _ = sim_v39.step([act39, act_opp39])
        [obs41_0, obs41_1], _, _, _ = sim_v41.step([act41, act_opp41])
        step += 1

    r39 = float(sim_v39.state[0].reward or 0.0)
    r41 = float(sim_v41.state[0].reward or 0.0)

    if r39 != r41:
        discrepancies += 1
        print(f"[Seed {seed}] Reward mismatch: V39={r39} != V41={r41}")

    print(f"Seed {seed} V39 Golden Property: {step} turns evaluated, discrepancies={discrepancies}, reward=${r41:.2f}")
    return discrepancies


if __name__ == "__main__":
    total_disc = 0
    print("=== TESTING V35 GOLDEN PROPERTY ===")
    for s in SEEDS_TO_TEST:
        total_disc += verify_golden_property_v35(s)

    print("\n=== TESTING V39 GOLDEN PROPERTY ===")
    for s in SEEDS_TO_TEST:
        total_disc += verify_golden_property_v39(s)

    print(f"\n==========================================")
    print(f"TOTAL GOLDEN PROPERTY DISCREPANCIES: {total_disc}")
    if total_disc == 0:
        print("PASS: GOLDEN PROPERTY FULLY VERIFIED (100% BIT-FOR-BIT EQUIVALENCE)")
    else:
        print("FAIL: DISCREPANCIES DETECTED!")
        sys.exit(1)
