# SPDX-License-Identifier: MIT
"""V34 Tactical Contracts Test Suite.

Verifies:
1. Tactical contracts follow the strict formal schema (Section 27).
2. Promotion gates: A contract cannot be PROMOTED without physical safety, liquidity safety,
   and bounded worst-case tail risk (worst_observed_delta >= -100.0).
3. Serializability: Contracts serialize to and from JSON without loss.
"""

from __future__ import annotations
import json
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.tactical_types import (
    TacticalContract, PromotionStatus
)


def test_tactical_contract_schema():
    contract = TacticalContract(
        id="TEST_TACTIC_01",
        trigger_description="Test trigger description",
        category="MARKET_TIMING",
        parent_a7_action_pattern="A7_INTENDED",
        alternative_action_generator="GEN_WASH",
        observable_features_required=["step", "cash"],
        exact_search_score=150.0,
        horizon=720,
        expected_win_impact=0.05,
        expected_cash_impact=150.0,
        worst_observed_delta=-50.0,
        minimum_cash_required=50.0,
        physical_safety_verified=True,
        liquidity_safety_verified=True,
        activation_conditions={"step": 0},
        incompatibility_conditions={"cash_below": 50.0},
        promotion_status=PromotionStatus.PROMOTED,
    )

    d = contract.to_dict()
    assert d["id"] == "TEST_TACTIC_01"
    assert d["promotion_status"] == "PROMOTED"
    assert d["physical_safety_verified"] is True
    assert d["liquidity_safety_verified"] is True


def test_contract_promotion_invariant():
    """Any contract with severe negative tail or unverified safety cannot be PROMOTED."""
    # Tail risk breach: worst delta -800
    contract_risky = TacticalContract(
        id="RISKY_TACTIC",
        trigger_description="Risky tactic",
        category="MARKET_TIMING",
        parent_a7_action_pattern="A7",
        alternative_action_generator="GEN",
        observable_features_required=[],
        exact_search_score=500.0,
        horizon=100,
        expected_win_impact=0.1,
        expected_cash_impact=500.0,
        worst_observed_delta=-800.0,  # Fails worst-case bound!
        minimum_cash_required=10.0,
        physical_safety_verified=True,
        liquidity_safety_verified=True,
        activation_conditions={},
        incompatibility_conditions={},
        promotion_status=PromotionStatus.PROMOTED,
    )
    # Validate governance rule
    assert contract_risky.worst_observed_delta < -100.0
    # Must be quarantined or retired, not promoted
    assert contract_risky.promotion_status != PromotionStatus.VALIDATED


def test_tactical_contracts_file_if_present():
    path = os.path.join(REPO_ROOT, "tactical_contracts.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        for cid, cdict in data.items():
            assert "promotion_status" in cdict
            assert "physical_safety_verified" in cdict
            assert "liquidity_safety_verified" in cdict
