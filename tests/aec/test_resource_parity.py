# SPDX-License-Identifier: MIT
"""Unit tests for AEC-RESOURCE Parity Harness (§20)."""

from __future__ import annotations

import copy
import pytest

from aec.counterfactual.simulator import SimulationOutcome
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch
from aec.resource.dag import ResourceEdge, ResourceNode, TemporalResourceDAG
from aec.resource.parity import ResourceParityHarness


def test_parity_exact_match(normal_opening_obs) -> None:
    """Validate exact agreement between symbolic DAG prediction and simulator outcome (§20)."""
    econ_state = build_economic_state(normal_opening_obs)
    dag = TemporalResourceDAG()
    dag.add_edge(ResourceEdge(
        edge_id="E_SELL",
        source_node_ids=["SHED_WHEAT"],
        dest_node_ids=["MONEY"],
        action_type="SELL",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": -1},
        cash_delta=25.0
    ))

    patch = CoupledPatch(
        patch_id="PATCH_SELL",
        source_opportunity_id="OPP_1",
        market_mutations=[["SELL", "WHEAT", 1]]
    )

    outcome = SimulationOutcome(
        candidate_final_money=3025.0,
        baseline_final_money=3000.0,
        delta_our_money=25.0, # Exactly matches +25.0
        candidate_opp_final_money=3000.0,
        baseline_opp_final_money=3000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=25.0,
        candidate_overflow_units=0,
        candidate_sold={"WHEAT": 1},
        baseline_sold={"WHEAT": 0},
        intermediate_solvency_ok=True,
        horizon=1
    )

    harness = ResourceParityHarness()
    report = harness.verify_parity(dag, patch, outcome, econ_state)

    assert report.is_exact_match
    assert report.fidelity_status == "VERIFIED"
    assert len(report.divergences) == 0


def test_parity_detects_cash_divergence(normal_opening_obs) -> None:
    """Validate parity harness detects cash delta discrepancies (§20)."""
    econ_state = build_economic_state(normal_opening_obs)
    dag = TemporalResourceDAG()
    dag.add_edge(ResourceEdge(
        edge_id="E_SELL",
        source_node_ids=["SHED_WHEAT"],
        dest_node_ids=["MONEY"],
        action_type="SELL",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": -1},
        cash_delta=50.0 # Symbolic claims $50
    ))

    patch = CoupledPatch(patch_id="P1", source_opportunity_id="O1")
    outcome = SimulationOutcome(
        candidate_final_money=3025.0,
        baseline_final_money=3000.0,
        delta_our_money=25.0, # Realized is only $25
        candidate_opp_final_money=3000.0,
        baseline_opp_final_money=3000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=25.0,
        candidate_overflow_units=0,
        candidate_sold={"WHEAT": 1},
        baseline_sold={"WHEAT": 0},
        intermediate_solvency_ok=True,
        horizon=1
    )

    harness = ResourceParityHarness()
    report = harness.verify_parity(dag, patch, outcome, econ_state)

    assert not report.is_exact_match
    assert any("Cash delta mismatch" in d for d in report.divergences)


def test_parity_detects_unmodeled_overflow(normal_opening_obs) -> None:
    """Validate parity harness catches unmodeled simulator overflow discards (§20)."""
    econ_state = build_economic_state(normal_opening_obs)
    dag = TemporalResourceDAG()
    patch = CoupledPatch(patch_id="P1", source_opportunity_id="O1")

    outcome = SimulationOutcome(
        candidate_final_money=3000.0,
        baseline_final_money=3000.0,
        delta_our_money=0.0,
        candidate_opp_final_money=3000.0,
        baseline_opp_final_money=3000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=3, # 3 units lost to shed overflow!
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=1
    )

    harness = ResourceParityHarness()
    report = harness.verify_parity(dag, patch, outcome, econ_state)

    assert not report.is_exact_match
    assert any("overflow discard" in d for d in report.divergences)
