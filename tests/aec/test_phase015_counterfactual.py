# SPDX-License-Identifier: MIT
"""Phase 015: Exact Counterfactual Evaluation & Negative Control Regression Tests.

Validates:
1. Positive counterfactual trajectory: Baseline emits no market sale, autonomous tranche
   candidate is synthesized, evaluated under exact counterfactual forward simulation,
   confirmed economically superior, passes safety certificate, and commits.
2. Negative control (downstream opportunity cost / inventory preservation): Under depressed
   or unfavorable conditions, exact counterfactual simulation or WinModel rejects liquidation.
3. Negative control (feed security): Wheat reservation preserves feed integrity; any
   candidate violating feed security is rejected by CounterfactualSimulator and SafetyCertificate.
4. Negative control (baseline already active): Baseline scheduling optimal sale causes
   synthesizer to defer, preventing redundant order spam.
5. Sequential market order lockstep: Synthesized sell prepended before buy executes solvently.
"""

from typing import Any, Dict
import pytest

from aec.config import (
    build_phase015_treatment_config,
    build_robust_qualified_config,
)
from aec.counterfactual.simulator import CounterfactualSimulator, CounterfactualFidelityLevel
from aec.evaluation.win_model import WinModel
from aec.events.detectors import detect_events
from aec.events.event_types import EventType
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.safety.checks import SafetyChecker


def _make_mock_obs(
    step: int = 300,
    shed: Dict[str, int] = None,
    prices: Dict[str, int] = None,
    cash: float = 200.0,
    animals: list = None,
) -> Dict[str, Any]:
    """Creates a canonical game observation dictionary matching kaggle engine."""
    shed_inv = shed or {"STRAWBERRY": 25, "WHEAT": 20}
    p_dict = prices or {"STRAWBERRY": 150, "WHEAT": 40, "CARROT": 50, "MELON": 120}
    full_prices = {
        "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
        "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
    }
    full_prices.update(p_dict)
    
    return {
        "step": step,
        "day": step // 24,
        "hour": step % 24,
        "player": 0,
        "farms": [
            {
                "money": cash,
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "animals": animals or [],
            },
            {
                "money": 3000.0,
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "animals": [],
            }
        ],
        "private": {
            "shed": shed_inv,
            "seeds": {},
            "inventories": [{}],
        },
        "market": {
            "prices": full_prices,
            "inventory": {p: 1000 for p in full_prices},
        },
        "town": {"unlocked_shops": []}
    }


class MockEmptyBackboneAdapter:
    """Mock backbone that emits empty market queue (reproducing V3 behavior)."""
    def __init__(self, config=None):
        self.config = config

    def call_once(self, obs, cfg=None):
        from aec.integration.backbone_adapter import BaselineResult
        step = int(obs.get("step", 0) or 0)
        return BaselineResult(
            step=step,
            action={"farmer": ["MOVE", "EAST"], "hands": [], "market": []},
            metadata={},
        )

    def get_future_trajectory(self, step, horizon=18, player=0, n_hands=0):
        return [{"farmer": ["MOVE", "EAST"], "hands": [], "market": []} for _ in range(horizon)]


class MockSellingBackboneAdapter:
    """Mock backbone that already emits a market sell action."""
    def __init__(self, config=None):
        self.config = config

    def call_once(self, obs, cfg=None):
        from aec.integration.backbone_adapter import BaselineResult
        step = int(obs.get("step", 0) or 0)
        return BaselineResult(
            step=step,
            action={"farmer": ["MOVE", "EAST"], "hands": [], "market": [["SELL", "STRAWBERRY", 10]]},
            metadata={},
        )

    def get_future_trajectory(self, step, horizon=18, player=0, n_hands=0):
        return [{"farmer": ["MOVE", "EAST"], "hands": [], "market": [["SELL", "STRAWBERRY", 10]]} for _ in range(horizon)]


def test_autonomous_tranche_positive_counterfactual_trajectory():
    """Regression Case: Baseline emits no sale; autonomous tranche produces positive exact trajectory and commits."""
    obs = _make_mock_obs(step=300, cash=50.0, shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 160})
    trt_cfg = build_phase015_treatment_config()

    adapter = MockEmptyBackboneAdapter(config=trt_cfg)
    executor = AECExecutor(backbone_adapter=adapter, config=trt_cfg)

    action = executor.act(obs)

    # 1. Action must have synthesized market sell
    assert action is not None
    assert "market" in action
    assert len(action["market"]) >= 1
    sell_order = action["market"][0]
    assert sell_order[0] == "SELL"
    assert sell_order[1] == "STRAWBERRY"
    assert 1 <= sell_order[2] <= 10

    # 2. Telemetry validation
    assert len(executor._telemetry_history) >= 1
    telem = executor._telemetry_history[-1]
    assert telem.decision == "COMMIT"
    assert telem.committed_mechanism == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"
    assert telem.simulations_run >= 1
    assert any("V3_WORKER_TRAVELING" in (c.why_v3_did_not_do_this or "") or "V3_PASSIVE_MARKET_QUEUE" in (c.why_v3_did_not_do_this or "") for c in telem.candidates)


def test_negative_control_feed_starvation_rejected_by_counterfactual():
    """Negative Control: Wheat candidate violating feed security is rejected by CounterfactualSimulator and Safety."""
    # Farm has 3 cows needing 3 wheat/day. Total wheat is only 3 units.
    animals = [
        {"kind": "COW", "fed_today": False, "consecutive_unfed": 1, "animal": {"type": "COW"}},
        {"kind": "COW", "fed_today": False, "consecutive_unfed": 1, "animal": {"type": "COW"}},
        {"kind": "COW", "fed_today": False, "consecutive_unfed": 1, "animal": {"type": "COW"}},
    ]
    # Set tiles with animals so simulator tracks daily feeding
    tiles = [[None]*10 for _ in range(10)]
    tiles[0][0] = {"kind": "COW", "animal": "COW", "fed_today": False, "consecutive_unfed": 1}
    tiles[0][1] = {"kind": "COW", "animal": "COW", "fed_today": False, "consecutive_unfed": 1}
    tiles[0][2] = {"kind": "COW", "animal": "COW", "fed_today": False, "consecutive_unfed": 1}

    obs = _make_mock_obs(step=23, cash=100.0, shed={"WHEAT": 3}, animals=animals)
    obs["farms"][0]["tiles"] = tiles
    econ = build_economic_state(obs)

    # Manually create a rogue/reckless candidate selling all 3 wheat
    rogue_patch = CoupledPatch(
        patch_id="ROGUE_FEED_SALE",
        source_opportunity_id="MOCK_OPP_01",
        mechanism_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
        market_mutations=[["SELL", "WHEAT", 3]],
    )

    sim = CounterfactualSimulator()
    outcome = sim.evaluate(
        candidate_patch=rogue_patch,
        baseline_action={"market": []},
        econ_state=econ,
        horizon=6,
    )

    # Simulator must catch feed security violation
    assert outcome.feed_security_ok is False
    assert outcome.fidelity == CounterfactualFidelityLevel.FAILED.value

    # Safety checker must reject
    safety = SafetyChecker()
    passed, checks, reason = safety.verify(
        patch=rogue_patch,
        outcome=outcome,
        econ_state=econ,
        baseline_action={"market": []},
    )
    assert passed is False
    assert "feed security" in reason.lower() or "fidelity" in reason.lower()


def test_negative_control_depressed_price_abstains():
    """Negative Control: When product price is depressed below threshold, trigger abstains and baseline executes."""
    # Strawberry base is 120, current price is 50 (ratio = 0.417 < 0.90)
    obs = _make_mock_obs(step=300, cash=500.0, shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 50})
    trt_cfg = build_phase015_treatment_config()

    adapter = MockEmptyBackboneAdapter(config=trt_cfg)
    executor = AECExecutor(backbone_adapter=adapter, config=trt_cfg)

    action = executor.act(obs)

    # Baseline market queue was empty; depressed price prevents liquidation
    assert action["market"] == []
    telem = executor._telemetry_history[-1]
    assert telem.decision == "BACKBONE"
    assert not telem.committed_mechanism


def test_negative_control_baseline_already_satisfies_optimal_sale():
    """Negative Control: When baseline already schedules optimal sale, synthesizer defers to avoid order spam."""
    obs = _make_mock_obs(step=300, cash=500.0, shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 150})
    trt_cfg = build_phase015_treatment_config()

    # Backbone already sells STRAWBERRY
    adapter = MockSellingBackboneAdapter(config=trt_cfg)
    executor = AECExecutor(backbone_adapter=adapter, config=trt_cfg)

    action = executor.act(obs)

    # Baseline order preserved without duplicating or creating conflicting sell
    assert action["market"] == [["SELL", "STRAWBERRY", 10]]
    telem = executor._telemetry_history[-1]
    assert telem.decision == "BACKBONE"


def test_sequential_market_order_lockstep():
    """Interleaved market order preserves sequential clearing: sell prepended before buy executes solvently."""
    obs = _make_mock_obs(step=300, cash=20.0, shed={"STRAWBERRY": 15}, prices={"STRAWBERRY": 150})
    trt_cfg = build_phase015_treatment_config()

    class MockBuyBackboneAdapter:
        def __init__(self, config=None):
            self.config = config
        def call_once(self, obs, cfg=None):
            from aec.integration.backbone_adapter import BaselineResult
            step = int(obs.get("step", 0) or 0)
            return BaselineResult(
                step=step,
                action={"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "FERTILIZER", 1]]},
                metadata={},
            )
        def get_future_trajectory(self, step, horizon=18, player=0, n_hands=0):
            return [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(horizon)]

    adapter = MockBuyBackboneAdapter(config=trt_cfg)
    executor = AECExecutor(backbone_adapter=adapter, config=trt_cfg)

    action = executor.act(obs)
    assert len(action["market"]) >= 2
    # Verify SELL comes before BUY to provide liquidity
    assert action["market"][0][0] == "SELL"
    assert action["market"][0][1] == "STRAWBERRY"
    assert action["market"][1][0] == "BUY_PRODUCT"
