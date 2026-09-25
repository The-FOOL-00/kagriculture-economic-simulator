# SPDX-License-Identifier: MIT
"""V34 Exact Forward Search Engine Test Suite.

Verifies:
1. ExactLocalSearchEngine executes paired counterfactual rollouts under identical seed/opponent.
2. Returns strongly typed TacticalOutcome with multi-horizon deltas (+4, +8, ..., terminal).
3. OpportunityLabel and HorizonTrajectory classifications are valid.
"""

from __future__ import annotations
import copy
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.search import ExactLocalSearchEngine
from candidates.v34_a7_tactical.tactical_types import (
    TacticalCandidate, PromotionStatus, OpportunityLabel, HorizonTrajectory
)


def test_search_engine_execution():
    engine = ExactLocalSearchEngine()
    
    # Define a simple step 0 wash candidate
    dummy_cand = TacticalCandidate(
        action_id="TEST_WASH_25",
        parent_a7_action={"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]},
        candidate_action={"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]},
        category="MARKET_TIMING",
        state_signature="STEP0_TEST",
        trigger_features={"step": 0.0},
        action_delta_description="Test wash resize to 25/25",
        status=PromotionStatus.EXPERIMENTAL,
    )

    outcome = engine.run_paired_counterfactual(
        seed=249675,
        opponent_id="SYN_AGG",
        seat=0,
        branch_step=0,
        candidate=dummy_cand,
    )

    assert outcome.candidate_id == "TEST_WASH_25"
    assert outcome.step == 0
    assert outcome.seed == 249675
    assert outcome.deltas.delta_terminal is not None
    assert isinstance(outcome.deltas.trajectory, HorizonTrajectory)
    assert isinstance(outcome.opportunity_label, OpportunityLabel)
    assert outcome.min_cash >= 0.0
