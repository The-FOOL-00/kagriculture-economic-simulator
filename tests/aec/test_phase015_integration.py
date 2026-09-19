# SPDX-License-Identifier: MIT
"""Phase 015: End-to-End Capability Integration & Governance Tests."""

import copy
import pytest
from typing import Any, Dict

from aec.config import (
    AECConfig,
    ENABLED_FOUNDATION_MECHANISMS,
    QUARANTINED_MECHANISMS,
    build_robust_qualified_config,
    build_phase015_treatment_config,
)
from aec.events.detectors import detect_events
from aec.events.event_types import EventType
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches.generator import PatchGenerator


def _make_mock_obs(
    step: int = 300,
    shed: Dict[str, int] = None,
    prices: Dict[str, int] = None,
    cash: float = 4000.0,
    animals: list = None,
) -> Dict[str, Any]:
    """Creates a canonical game observation dictionary matching kaggle engine."""
    shed_inv = shed or {"STRAWBERRY": 40, "WHEAT": 20}
    p_dict = prices or {"STRAWBERRY": 145, "WHEAT": 40, "CARROT": 50, "MELON": 120}
    full_prices = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
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


class MockBackboneAdapter:
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


def test_frozen_control_foundation_invariance():
    """Control configuration must NOT activate Phase 015 mechanisms or quarantined mechanisms."""
    ctrl_cfg = build_robust_qualified_config()
    assert ctrl_cfg.frozen_mode is True
    assert ctrl_cfg.enable_asset_holding_trigger is False
    assert ctrl_cfg.enable_tranche_synthesizer is False
    assert "ASSET_HOLDING_VALUATION_TRIGGER" not in ctrl_cfg.enabled_mechanisms
    assert "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER" not in ctrl_cfg.enabled_mechanisms
    
    # Verify all 12 quarantined mechanisms are strictly in quarantined list
    for q in (
        "DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP", "RESOURCE_CONVERSION",
        "EMERGENCY_FEED_PURCHASE", "ROUTE_COMPRESSION", "CARGO_FERRY", "TOWN_CYCLE",
        "SHOP_ARBITRAGE", "PRODUCTION_ARBITRAGE", "TERMINAL_CONVERSION",
        "EMERGENCY_RECOVERY", "OPPONENT_PREEMPT_SELL"
    ):
        assert q in ctrl_cfg.quarantined_mechanisms


def test_treatment_config_composition():
    """Treatment configuration activates Phase 015 capabilities without activating quarantined mechanisms."""
    trt_cfg = build_phase015_treatment_config()
    assert trt_cfg.enable_asset_holding_trigger is True
    assert trt_cfg.enable_tranche_synthesizer is True
    assert "ASSET_HOLDING_VALUATION_TRIGGER" in trt_cfg.enabled_mechanisms
    assert "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER" in trt_cfg.enabled_mechanisms

    # Verify quarantined mechanisms remain quarantined in treatment
    for q in (
        "DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP", "RESOURCE_CONVERSION",
        "EMERGENCY_FEED_PURCHASE", "ROUTE_COMPRESSION", "CARGO_FERRY", "TOWN_CYCLE",
        "SHOP_ARBITRAGE", "PRODUCTION_ARBITRAGE", "TERMINAL_CONVERSION",
        "EMERGENCY_RECOVERY", "OPPONENT_PREEMPT_SELL"
    ):
        assert q in trt_cfg.quarantined_mechanisms


def test_asset_holding_detector_fires_without_deltas():
    """Verify Capability A detects persistent holding state even when delta_cash == 0 and delta_shed == 0."""
    obs = _make_mock_obs(step=300, shed={"STRAWBERRY": 40}, prices={"STRAWBERRY": 145})
    econ_state = build_economic_state(obs)
    
    trt_cfg = build_phase015_treatment_config()
    events = detect_events(econ_state, previous_state=econ_state, baseline_action={"market": []}, config=trt_cfg)
    
    event_types = [e.event_type for e in events]
    assert EventType.E13_ASSET_HOLDING_STATE in event_types

    opp_engine = OpportunityEngine(config=trt_cfg)
    opps = opp_engine.detect_opportunities(econ_state, events, baseline_action={"market": []}, config=trt_cfg)
    
    strawberry_opps = [o for o in opps if o.affected_entities and o.affected_entities[0] == "STRAWBERRY"]
    assert len(strawberry_opps) >= 1
    assert strawberry_opps[0].candidate_transformation_family == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"


def test_autonomous_tranche_synthesis_from_empty_queue():
    """Verify Capability B synthesizes valid market order when baseline market queue is empty."""
    obs = _make_mock_obs(step=300, shed={"STRAWBERRY": 40}, prices={"STRAWBERRY": 145})
    econ_state = build_economic_state(obs)
    trt_cfg = build_phase015_treatment_config()
    
    opp_engine = OpportunityEngine(config=trt_cfg)
    events = [detect_events(econ_state, config=trt_cfg)[0]]
    opps = opp_engine.detect_opportunities(econ_state, events, baseline_action={"market": []}, config=trt_cfg)
    
    generator = PatchGenerator(config=trt_cfg)
    patches = generator.generate_patches(opps, econ_state, baseline_action={"farmer": ["PASS"], "market": []}, config=trt_cfg)
    
    assert len(patches) >= 1
    synth_patch = patches[0]
    assert synth_patch.mechanism_family == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"
    assert len(synth_patch.market_mutations) >= 1
    order = synth_patch.market_mutations[0]
    assert order[0] == "SELL"
    assert order[1] == "STRAWBERRY"
    assert 1 <= order[2] <= 10


def test_end_to_end_executor_with_treatment():
    """Verify AECExecutor pipeline end-to-end with treatment configuration."""
    obs = _make_mock_obs(step=300, shed={"STRAWBERRY": 50}, prices={"STRAWBERRY": 150})
    trt_cfg = build_phase015_treatment_config()
    
    mock_adapter = MockBackboneAdapter(config=trt_cfg)
    executor = AECExecutor(backbone_adapter=mock_adapter, config=trt_cfg)
    
    action = executor.act(obs)
    assert action is not None
    # Telemetry must show candidate proposed and evaluated
    last_telem = executor._telemetry_history[-1]
    assert last_telem.step == 300
    assert "E13_ASSET_HOLDING_STATE" in last_telem.events_detected
    assert last_telem.opportunities_count >= 1
    assert last_telem.candidates_count >= 1
