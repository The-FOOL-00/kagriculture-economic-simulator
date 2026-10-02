#!/usr/bin/env python3
"""Audit Golden Property: verify that V49 is bit-for-bit identical to V48 across steps 0..623."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v48_challenger.main as v48_mod
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

SEEDS = [250300 + i for i in range(20)]

def main():
    print("Auditing Golden Property: V49 vs V48 across 20 matches (steps 0..623)...")
    total_turns = 0
    divergences = 0

    for idx, seed in enumerate(SEEDS):
        sim = FastKagricultureSim(seed=seed)
        obs = sim.reset(seed=seed)
        for step in range(624):
            a_v48 = v48_mod.agent(obs[0])
            a_v49 = v49_mod.agent(obs[0])
            total_turns += 1
            if a_v48 != a_v49:
                divergences += 1
                print(f"DIVERGENCE at seed {seed}, step {step}: V48={a_v48} != V49={a_v49}")
            # Step sim with v48 to advance world
            a_opp = v44_mod.agent(obs[1])
            obs, _, _, _ = sim.step([a_v48, a_opp])

    print(f"\nAudit Complete: {total_turns} turns checked.")
    print(f"Divergences found (steps 0..623): {divergences}")
    assert divergences == 0, "CRITICAL: V49 broke Golden Property invariance with V48!"
    print("GOLDEN PROPERTY VERIFIED: 100.0% bit-for-bit identity across turns 0..623!")

if __name__ == "__main__":
    main()
