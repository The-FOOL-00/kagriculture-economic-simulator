#!/usr/bin/env python3
"""Golden Property Verification for Kagriculture V48.

Verifies Part 33 of the V48 mandate:
"If the patch does not activate: V48 == 2945 bit-for-bit.
Verify: >=20 full matches, >=10,000 turns, 0 unexpected differences for the abstention path."
"""

import copy
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945
import candidates.v48_challenger.main as mv48

# Seeds to test
candidate_seeds = [249800 + i for i in range(50)]
abstention_matches_verified = 0
total_turns = 0
differences = 0

print("Finding and verifying 20 full abstention matches (where _V48_OVERRIDES is inactive)...")

for seed in candidate_seeds:
    if abstention_matches_verified >= 20:
        break

    # First run up to step 144 to inspect unlocked shops
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    for _ in range(144):
        a = m2945.agent(obs[0])
        obs, _, _, _ = sim.step([a, {"farmer": ["PASS"], "hands": [], "market": []}])

    town = obs[0].get("town", {}) or {}
    shops = tuple((town.get("unlocked_shops", []) or [])[:2])

    if shops in mv48._V48_OVERRIDES:
        # Active override seed, skip for abstention verification
        continue

    # Pure abstention match: re-simulate full 719 turns from scratch
    abstention_matches_verified += 1
    sim_full = FastKagricultureSim(seed=seed)
    obs_full = sim_full.reset(seed=seed)

    for step in range(719):
        obs_0 = copy.deepcopy(obs_full[0])
        obs_1 = copy.deepcopy(obs_full[0])

        act_2945 = m2945.agent(obs_0)
        act_v48 = mv48.agent(obs_1)

        total_turns += 1
        if act_2945 != act_v48:
            differences += 1
            print(f"DIFF at seed={seed} step={step}: 2945={act_2945} vs v48={act_v48}")

        obs_full, _, _, _ = sim_full.step([act_2945, {"farmer": ["PASS"], "hands": [], "market": []}])

print(f"\nGolden Property Verification Complete:")
print(f"Total Abstention Matches Verified: {abstention_matches_verified}")
print(f"Total Turns Evaluated: {total_turns}")
print(f"Unexpected Differences: {differences}")

assert differences == 0, f"FAILED: Golden property violated with {differences} differences!"
assert abstention_matches_verified >= 20, f"FAILED: Only {abstention_matches_verified} matches verified!"
assert total_turns >= 10000, f"FAILED: Only {total_turns} turns verified!"
print("GOLDEN PROPERTY VERIFIED: V48 == 2945 bit-for-bit across all abstention games!")
