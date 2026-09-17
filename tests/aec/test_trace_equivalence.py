# SPDX-License-Identifier: MIT
"""Integration tests for Trace-Equivalence Parity Harness (§13)."""

from __future__ import annotations

import pytest
from aec.counterfactual.parity_harness import TraceEquivalenceHarness


def test_trace_equivalence_multi_step():
    """Verifies that TraceEquivalenceHarness correctly compares real engine vs CF simulator."""
    harness = TraceEquivalenceHarness()
    
    # Test step 10 on dev seed 101
    res = harness.run_turn_parity_comparison(
        seed=101,
        step=10,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 4]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()

    # Test step 20 on dev seed 102
    res2 = harness.run_turn_parity_comparison(
        seed=102,
        step=20,
        player_action={"market": [["BUY_PRODUCT", "FERTILIZER", 2]]},
        opponent_action={"market": []}
    )
    assert res2.passed, res2.summary()
