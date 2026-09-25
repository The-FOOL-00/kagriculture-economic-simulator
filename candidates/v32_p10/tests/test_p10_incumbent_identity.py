# SPDX-License-Identifier: MIT
"""V32 P10 Incumbent Identity & Freeze Invariant Tests.

Verifies:
1. A7 standalone package integrity and SHA-256 hash.
2. Step-0 30/30 wheat wash opening mechanism preservation.
3. Bit-level action identity over initial 25 steps between pure A7 and P10 (residual disabled).
4. Exact terminal cash parity ($0.00 paired delta) on development panel episodes across both seats.
"""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kaggle_environments import make
from v32_common import DIGESTS, PATHS, assert_frozen, check_seed_allowed, load_agent, sha256_file
from candidates.v32_p10.config import P10Config
from candidates.v32_p10.incumbent import load_fresh_a7
from candidates.v32_p10.main import make_p10_agent


def test_a7_standalone_freeze_integrity():
    """Verify A7 package hash matches frozen V32 baseline."""
    assert_frozen()
    path = os.path.join(REPO_ROOT, PATHS["a7_standalone"])
    assert sha256_file(path) == DIGESTS["a7_standalone"]


def test_step0_opening_identity():
    """Verify step 0 30-wash preservation in closed-loop play for pure A7 and P10."""
    seed = 249675
    check_seed_allowed(seed)
    expected_wash = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
    
    # Run 5 steps of pure A7 vs V3
    env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 5}, debug=False)
    a7_fn = load_fresh_a7()
    opp_fn1 = load_agent("E0_V3")
    env_a7.run([a7_fn, opp_fn1])
    act_a7 = env_a7.steps[1][0]["action"].get("market") or []
    
    # Run 5 steps of P10 (residual disabled) vs V3
    env_p10 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 5}, debug=False)
    p10_fn, _ = make_p10_agent(config=P10Config(residual_enabled=False))
    opp_fn2 = load_agent("E0_V3")
    env_p10.run([p10_fn, opp_fn2])
    act_p10 = env_p10.steps[1][0]["action"].get("market") or []
    
    assert act_a7 == expected_wash, f"A7 step 0 wash mismatch: {act_a7} != {expected_wash}"
    assert act_p10 == expected_wash, f"P10 step 0 wash mismatch: {act_p10} != {expected_wash}"
    assert act_p10 == act_a7, "P10 action at step 0 is not identical to A7"


def test_first_25_steps_bit_level_identity():
    """Verify bit-for-bit action identity across the first 25 steps."""
    seed = 249675
    check_seed_allowed(seed)
    
    # Run pure A7 vs V3 for 27 steps (steps 0..25 executed)
    env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 27}, debug=False)
    a7_fn = load_fresh_a7()
    v3_fn_1 = load_agent("E0_V3")
    env_a7.run([a7_fn, v3_fn_1])
    
    # Run P10 (residual disabled) vs V3 for 27 steps
    env_p10 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 27}, debug=False)
    p10_fn, _ = make_p10_agent(config=P10Config(residual_enabled=False))
    v3_fn_2 = load_agent("E0_V3")
    env_p10.run([p10_fn, v3_fn_2])
    
    # Compare every action from step 1 to step 26 (environment records step t action at steps[t+1])
    for step_idx in range(1, len(env_a7.steps)):
        act_a7 = env_a7.steps[step_idx][0].get("action") or {}
        act_p10 = env_p10.steps[step_idx][0].get("action") or {}
        assert act_p10 == act_a7, f"Action divergence at step index {step_idx}:\nA7:  {act_a7}\nP10: {act_p10}"
        
        # Verify money and tiles match exactly
        money_a7 = env_a7.steps[step_idx][0]["observation"]["farms"][0]["money"]
        money_p10 = env_p10.steps[step_idx][0]["observation"]["farms"][0]["money"]
        assert money_p10 == money_a7, f"Money divergence at step index {step_idx}: A7={money_a7}, P10={money_p10}"


@pytest.mark.parametrize("seed", [249675, 249676])
@pytest.mark.parametrize("seat", [0, 1])
def test_full_episode_paired_parity(seed, seat):
    """Verify exact full-episode terminal parity between A7 and P10-disabled."""
    check_seed_allowed(seed)
    
    # 1. Full match with pure A7
    a7_fn = load_fresh_a7()
    opp_fn_1 = load_agent("E0_V3")
    agents_a7 = [a7_fn, opp_fn_1] if seat == 0 else [opp_fn_1, a7_fn]
    env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_a7.run(agents_a7)
    cash_a7 = float(env_a7.steps[-1][seat]["reward"] or 0.0)
    
    # 2. Full match with P10 (residual disabled)
    p10_fn, _ = make_p10_agent(config=P10Config(residual_enabled=False))
    opp_fn_2 = load_agent("E0_V3")
    agents_p10 = [p10_fn, opp_fn_2] if seat == 0 else [opp_fn_2, p10_fn]
    env_p10 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_p10.run(agents_p10)
    cash_p10 = float(env_p10.steps[-1][seat]["reward"] or 0.0)
    
    delta = cash_p10 - cash_a7
    assert delta == 0.0, f"Parity failure on Seed {seed} Seat {seat}: P10=${cash_p10} vs A7=${cash_a7} (Delta=${delta})"
