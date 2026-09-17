# SPDX-License-Identifier: MIT
"""Tests for AEC Multi-Step Counterfactual Continuation (§3, §10, §11, §16).

Verifies that the counterfactual simulator produces a valid, deterministic,
multi-turn continuation rather than defaulting to PASS and empty market orders.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List
import pytest

from aec.counterfactual.simulator import CounterfactualSimulator, simulate_rollout
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


class MockCallCountingBackbone:
    """Mock backbone that counts live invocations and exposes a future route tape."""

    def __init__(self, action: Dict[str, Any], future_schedule: List[Dict[str, Any]]) -> None:
        self.action = action
        self.schedule = [action] + future_schedule
        self.call_count = 0

    def __call__(self, obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
        self.call_count += 1
        return copy.deepcopy(self.action)


def test_1_multi_step_worker_continuation(normal_opening_obs: Dict[str, Any]) -> None:
    """TEST 1: Worker does not freeze after offset 0; position advances over later offsets."""
    state = build_economic_state(normal_opening_obs)
    # Farmer starts at [4, 4]
    initial_action = {"farmer": ["SOUTH"], "hands": [], "market": []}
    continuation = [
        {"farmer": ["SOUTH"], "hands": [], "market": []},  # offset 1 -> [4, 6]
        {"farmer": ["EAST"], "hands": [], "market": []},   # offset 2 -> [5, 6]
        {"farmer": ["EAST"], "hands": [], "market": []},   # offset 3 -> [6, 6]
    ]

    simulator = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="P_WORKER_TEST",
        source_opportunity_id="OPP_TEST",
        worker_mutations={0: ["SOUTH"]},
        expected_horizon=4
    )

    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=initial_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation,
        trace=True
    )

    trace = outcome.baseline_trace
    assert trace is not None
    assert len(trace) == 4

    # Assert worker positions advance across offsets
    assert trace[0]["worker_positions"][0] == [4, 5]
    assert trace[1]["worker_positions"][0] == [4, 6]
    assert trace[2]["worker_positions"][0] == [5, 6]
    assert trace[3]["worker_positions"][0] == [6, 6]

    # Assert actions are not replaced by PASS
    assert trace[1]["worker_actions"][0] == ["SOUTH"]
    assert trace[2]["worker_actions"][0] == ["EAST"]
    assert trace[3]["worker_actions"][0] == ["EAST"]


def test_2_baseline_continuation(normal_opening_obs: Dict[str, Any]) -> None:
    """TEST 2: Baseline trajectory itself continues actively across H >= 4."""
    state = build_economic_state(normal_opening_obs)
    initial_action = {"farmer": ["EAST"], "hands": [], "market": []}
    continuation = [
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["SOUTH"], "hands": [], "market": []},
        {"farmer": ["SOUTH"], "hands": [], "market": []},
        {"farmer": ["WEST"], "hands": [], "market": []},
    ]

    simulator = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="P_DUMMY",
        source_opportunity_id="OPP_DUMMY",
        market_mutations=[],
        expected_horizon=6
    )

    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=initial_action,
        econ_state=state,
        horizon=6,
        continuation_trajectory=continuation,
        trace=True
    )

    trace = outcome.baseline_trace
    assert trace is not None
    assert len(trace) == 6
    # Positions: [4, 4] -> [5, 4] -> [6, 4] -> [7, 4] -> [7, 5] -> [7, 6] -> [6, 6]
    positions = [t["worker_positions"][0] for t in trace]
    assert positions == [[5, 4], [6, 4], [7, 4], [7, 5], [7, 6], [6, 6]]


def test_3_candidate_backbone_fairness(normal_opening_obs: Dict[str, Any]) -> None:
    """TEST 3: Baseline and candidate receive equivalent continuation after local patch."""
    state = build_economic_state(normal_opening_obs)
    baseline_action = {"farmer": ["SOUTH"], "hands": [], "market": []}
    continuation = [
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["NORTH"], "hands": [], "market": []},
    ]

    # Patch changes only offset 0 action from SOUTH to PASS
    patch = CoupledPatch(
        patch_id="P_FAIRNESS",
        source_opportunity_id="OPP_FAIRNESS",
        worker_mutations={0: ["PASS"]},
        expected_horizon=4
    )

    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation,
        trace=True
    )

    b_trace = outcome.baseline_trace
    c_trace = outcome.candidate_trace
    assert b_trace is not None and c_trace is not None

    # Offset 0 reflects the local patch difference
    assert b_trace[0]["worker_actions"][0] == ["SOUTH"]
    assert c_trace[0]["worker_actions"][0] == ["PASS"]
    assert b_trace[0]["worker_positions"][0] == [4, 5]
    assert c_trace[0]["worker_positions"][0] == [4, 4]

    # Under Fix C (Spatial Consistency Guard), candidate detects position divergence
    # from baseline route tape and safely truncates stale continuation commands
    assert outcome.spatial_consistency_ok is False
    assert "spatially desynchronized" in outcome.desynchronization_reason

    # Baseline receives continuation, candidate truncates stale spatial commands to PASS
    for offset in range(1, 4):
        assert b_trace[offset]["worker_actions"][0] == continuation[offset - 1]["farmer"]
        assert c_trace[offset]["worker_actions"][0] == ["PASS"]



def test_4_market_continuation(shed_capacity_obs: Dict[str, Any]) -> None:
    """TEST 4: Market inventory and cash evolve across offsets without collapsing to empty."""
    state = build_economic_state(shed_capacity_obs)
    # Shed has 90 STRAWBERRY
    initial_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    continuation = [
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
    ]

    simulator = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="P_MARKET",
        source_opportunity_id="OPP_MARKET",
        market_mutations=[],
        expected_horizon=4
    )

    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=initial_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation,
        trace=True
    )

    trace = outcome.baseline_trace
    assert trace is not None
    assert len(trace) == 4

    # Offset 0: no sales
    assert trace[0]["shed"]["STRAWBERRY"] == 90
    initial_cash = trace[0]["cash"]

    # Offset 1: 10 sold
    assert trace[1]["shed"]["STRAWBERRY"] == 80
    assert trace[1]["cash"] > initial_cash

    # Offset 2: another 10 sold
    assert trace[2]["shed"]["STRAWBERRY"] == 70
    assert trace[2]["cash"] > trace[1]["cash"]

    # Offset 3: another 10 sold
    assert trace[3]["shed"]["STRAWBERRY"] == 60
    assert trace[3]["cash"] > trace[2]["cash"]


def test_5_state_propagation(shed_capacity_obs: Dict[str, Any]) -> None:
    """TEST 5: Action change at offset 0 propagates deterministically to offsets 1, 2, and H."""
    state = build_economic_state(shed_capacity_obs)
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    continuation = [
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 20]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
    ]

    # Candidate sells 15 STRAWBERRY at offset 0
    patch = CoupledPatch(
        patch_id="P_PROPAGATION",
        source_opportunity_id="OPP_PROPAGATION",
        market_mutations=[["SELL", "STRAWBERRY", 15]],
        expected_horizon=4
    )

    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation,
        trace=True
    )

    b_trace = outcome.baseline_trace
    c_trace = outcome.candidate_trace
    assert b_trace is not None and c_trace is not None

    # Offset 0: candidate sold 15, baseline sold 0
    assert c_trace[0]["cash"] > b_trace[0]["cash"]
    assert c_trace[0]["shed"]["STRAWBERRY"] == b_trace[0]["shed"]["STRAWBERRY"] - 15

    # Offset 1: passive continuation, state delta persists
    assert c_trace[1]["cash"] > b_trace[1]["cash"]
    assert c_trace[1]["shed"]["STRAWBERRY"] == b_trace[1]["shed"]["STRAWBERRY"] - 15

    # Offset 2: both execute market sell of 20
    assert c_trace[2]["shed"]["STRAWBERRY"] == b_trace[2]["shed"]["STRAWBERRY"] - 15

    # Offset 3: final outcome preserves difference
    assert outcome.candidate_final_money > outcome.baseline_final_money


def test_6_candidate_isolation(terminal_proximity_obs: Dict[str, Any]) -> None:
    """TEST 6: Candidate A continuation does not mutate or contaminate baseline or Candidate B."""
    state = build_economic_state(terminal_proximity_obs)
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    continuation = [
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(5)
    ]

    patch_A = CoupledPatch(
        patch_id="PATCH_A",
        source_opportunity_id="OPP_A",
        market_mutations=[["SELL", "STRAWBERRY", 5]],
        expected_horizon=6
    )
    patch_B = CoupledPatch(
        patch_id="PATCH_B",
        source_opportunity_id="OPP_B",
        market_mutations=[["SELL", "WOOL", 8]],
        expected_horizon=6
    )

    simulator = CounterfactualSimulator()
    outcome_A1 = simulator.evaluate(patch_A, baseline_action, state, 6, continuation, trace=True)
    outcome_B = simulator.evaluate(patch_B, baseline_action, state, 6, continuation, trace=True)
    outcome_A2 = simulator.evaluate(patch_A, baseline_action, state, 6, continuation, trace=True)

    # Baseline trace is identical across all evaluations
    assert outcome_A1.baseline_final_money == outcome_B.baseline_final_money
    assert outcome_A1.baseline_final_money == outcome_A2.baseline_final_money

    # Candidate A outcomes are identical
    assert outcome_A1.candidate_final_money == outcome_A2.candidate_final_money
    assert outcome_A1.delta_our_money == outcome_A2.delta_our_money
    assert outcome_A1.candidate_trace == outcome_A2.candidate_trace


def test_7_deterministic_replay(weed_obstruction_obs: Dict[str, Any]) -> None:
    """TEST 7: Identical input state, patch, and continuation yield 100% bit-identical traces."""
    state = build_economic_state(weed_obstruction_obs)
    baseline_action = {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []}
    continuation = [
        {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []},
        {"farmer": ["DOWN"], "hands": [["LEFT"]], "market": []},
        {"farmer": ["DOWN"], "hands": [["PASS"]], "market": []},
    ]
    patch = CoupledPatch(
        patch_id="PATCH_REPLAY",
        source_opportunity_id="OPP_REPLAY",
        worker_mutations={0: ["DIG"]},
        expected_horizon=4
    )

    simulator = CounterfactualSimulator()
    runs = [
        simulator.evaluate(patch, baseline_action, state, 4, continuation, trace=True)
        for _ in range(3)
    ]

    for i in range(1, len(runs)):
        assert runs[0].baseline_final_money == runs[i].baseline_final_money
        assert runs[0].candidate_final_money == runs[i].candidate_final_money
        assert runs[0].baseline_trace == runs[i].baseline_trace
        assert runs[0].candidate_trace == runs[i].candidate_trace


def test_8_terminal_boundary(terminal_proximity_obs: Dict[str, Any]) -> None:
    """TEST 8: Simulator does not execute impossible steps past step 719 and remains fail-closed."""
    # terminal_proximity_obs has step=718. Game ends at step 719.
    state = build_economic_state(terminal_proximity_obs)
    assert state.step == 718

    # Request H=8 when only 2 steps (718 and 719) remain before terminal boundary (720)
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    continuation = [
        {"farmer": ["RIGHT"], "hands": [["PASS"]], "market": []} for _ in range(7)
    ]
    patch = CoupledPatch(
        patch_id="PATCH_TERM",
        source_opportunity_id="OPP_TERM",
        market_mutations=[["SELL", "STRAWBERRY", 5]],
        expected_horizon=8
    )

    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=8,
        continuation_trajectory=continuation,
        trace=True
    )

    # Must clamp at step 720: exactly 2 offsets simulated (offset 0 at 718, offset 1 at 719)
    assert len(outcome.baseline_trace) == 2
    assert outcome.baseline_trace[0]["step"] == 718
    assert outcome.baseline_trace[1]["step"] == 719
    assert outcome.intermediate_solvency_ok is True


def test_9_one_baseline_call_with_continuation(weed_obstruction_obs: Dict[str, Any]) -> None:
    """TEST 9: Multi-step continuation does NOT introduce additional live V3/backbone calls."""
    initial_action = {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []}
    future_schedule = [
        {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []} for _ in range(20)
    ]
    mock_backbone = MockCallCountingBackbone(initial_action, future_schedule)
    adapter = BackboneAdapter(v3_callable=mock_backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    # act() will detect events, generate candidates, and run multi-step H=6/18 simulations
    action = executor.act(weed_obstruction_obs)

    # Exactly ONE live call must have occurred
    assert mock_backbone.call_count == 1
    assert action is not None
    assert executor.latest_telemetry is not None
    assert executor.latest_telemetry.simulations_run > 0


def test_10_no_event_baseline(normal_opening_obs: Dict[str, Any]) -> None:
    """TEST 10: AEC dormant/no-event output remains bit-identical to baseline action."""
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}
    mock_backbone = MockCallCountingBackbone(baseline_action, [])
    adapter = BackboneAdapter(v3_callable=mock_backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    result_action = executor.act(normal_opening_obs)

    assert result_action == baseline_action
    assert executor.latest_telemetry.decision == "BACKBONE"
    assert executor.latest_telemetry.abstain_reason == "NO_EVENT_FAST_PATH"
    assert mock_backbone.call_count == 1
