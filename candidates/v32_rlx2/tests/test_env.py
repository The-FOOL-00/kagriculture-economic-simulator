# SPDX-License-Identifier: MIT
"""Unit and integration tests for candidates/v32_rlx2/env.py."""

import os
import sys
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RLX2_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from candidates.v32_rlx2.rlx2_config import RLX2Config, V32_DEV_HIST
from candidates.v32_rlx2.env import RLX2Env
from candidates.v32_rlx2.state import get_feature_dim
from candidates.v32_rlx2.action_space import ACTION_SPACE_SIZE
from scripts.v32_common import assert_frozen, load_agent
from kaggle_environments import make


def test_frozen_integrity():
    """Verify all frozen repository dependencies remain bit-identical."""
    assert_frozen()


def test_feature_dimensions():
    """Verify feature vector shapes across S0, S1, S2, S3 tiers."""
    for tier, expected_dim in [("S0", 19), ("S1", 63), ("S2", 71), ("S3", 80)]:
        dim = get_feature_dim(tier)
        assert dim == expected_dim, f"Tier {tier} expected {expected_dim}, got {dim}"


def test_action_0_bit_identical_to_a7():
    """CRITICAL TEST: When agent selects action 0 (FOLLOW_A7), the final cash
    must match protected incumbent A7 down to the exact dollar ($0.00 delta)."""
    cfg = RLX2Config(macro_interval=4, reward_mode="R0")
    env = RLX2Env(config=cfg)
    
    test_seed = V32_DEV_HIST[0]  # 249675
    
    # 1. Run pure A7 standalone baseline
    a7_agent = load_agent("E9_AST")
    v3_opp = load_agent("E0_V3")
    k_env = make("kaggriculture", configuration={"seed": test_seed})
    k_env.run([lambda o, c=None: a7_agent.act(o, c), lambda o, c=None: v3_opp.act(o, c)])
    a7_expected_cash = float(k_env.steps[-1][0]["reward"])
    
    # 2. Run RLX2Env with pure Action 0 (FOLLOW_A7)
    obs, mask = env.reset(seed=test_seed, opponent_id="E0_V3", seat=0)
    assert mask[0] is True or mask[0] == 1
    
    done = False
    total_reward = 0.0
    while not done:
        obs, reward, done, info = env.step(0)
        total_reward += reward
        assert obs is not None
        assert np.all(np.isfinite(obs))
        assert mask[0] is True or mask[0] == 1
        
    final_cash = info["final_cash"]
    assert final_cash == a7_expected_cash, f"RLX2 FOLLOW_A7 mismatch: got {final_cash}, expected {a7_expected_cash}"
    print(f"\n[PASS] Seed {test_seed}: Pure Action 0 matches A7 exactly: ${final_cash:,.2f}")
