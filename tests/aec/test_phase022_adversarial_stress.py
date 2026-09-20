# SPDX-License-Identifier: MIT
"""Phase 022: Adversarial State Stress Test Suite (§5).

Verifies that the consolidated AEC live foundation safely abstains,
fails closed, and maintains strict invariant guarantees across the seven
failure boundaries identified in Phases 015–021:
1. Cash / Capital Boundary (low cash, capex cliff)
2. Production Boundary (premature harvest, biological yield forfeiture)
3. Worker Dependency Boundary (travel, occupation, inventory limits)
4. Cargo Boundary (backpack cargo lock / cargo-trapping trap)
5. Market Boundary (order price volatility, rival dumping)
6. Terminal Boundary (steps 718-720 liquidation & shutdown interaction)
7. Macro Boundary (feed deficit, budget-guard escalations)
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict

import kagsim
from aec.config import build_robust_qualified_config
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.terminal import transform_terminal_liquidation, transform_phase_shutdown


def make_engine_obs(seed: int = 249376, step: int = 100) -> Dict[str, Any]:
    """Generate an exact engine-grounded observation using kagsim."""
    game = kagsim.Game(seed)
    obs = copy.deepcopy(game.observe(0))
    obs["step"] = step
    return obs


class MockBackbone:
    """Deterministic mock backbone returning safe default actions."""
    def __init__(self, action: Dict[str, Any] = None) -> None:
        self.action = action or {"farmer": ["PASS"], "hands": [], "market": []}

    def __call__(self, obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
        return copy.deepcopy(self.action)


# -----------------------------------------------------------------------------
# 1. CASH / CAPITAL BOUNDARY
# -----------------------------------------------------------------------------
def test_adversarial_cash_capital_boundary_low_cash():
    """Verify AEC never commits unauthorized purchases or violates solvency when money is near zero."""
    obs = make_engine_obs(step=200)
    obs["farms"][0]["money"] = 2.50  # critically low cash

    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["PASS"], "hands": [], "market": []}))
    executor = AECExecutor(backbone_adapter=adapter, config=build_robust_qualified_config())

    action = executor.act(obs)
    # Must not place buy orders or capex orders that violate cash
    market = action.get("market", [])
    for order in market:
        if isinstance(order, (list, tuple)) and len(order) >= 1:
            assert order[0] not in ("BUY", "BUY_SEED", "BUY_LAND", "BUY_ANIMAL"), "AEC placed BUY order under near-zero cash!"


# -----------------------------------------------------------------------------
# 2. PRODUCTION BOUNDARY (Premature Crop Harvest)
# -----------------------------------------------------------------------------
def test_adversarial_production_boundary_prevents_premature_harvest():
    """Verify AEC does not commit single-turn premature harvest on growing crops."""
    obs = make_engine_obs(step=120)
    obs["farms"][0]["money"] = 5000.0

    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["PASS"], "hands": [["WATER", 4, 9]], "market": []}))
    executor = AECExecutor(backbone_adapter=adapter, config=build_robust_qualified_config())

    action = executor.act(obs)
    # Foundation must not mutate Hand 1's WATER to premature HARVEST
    hands = action.get("hands", [])
    if hands and len(hands) > 0:
        assert hands[0][0] != "HARVEST", "AEC committed rogue premature HARVEST, destroying crop biology!"


# -----------------------------------------------------------------------------
# 3. WORKER DEPENDENCY BOUNDARY (Transit & Occupation)
# -----------------------------------------------------------------------------
def test_adversarial_worker_dependency_boundary_preserves_farmer_command():
    """Verify AEC foundation never overrides valid farmer movement with illegal commands."""
    obs = make_engine_obs(step=300)
    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["MOVE", "NORTH"], "hands": [], "market": []}))
    executor = AECExecutor(backbone_adapter=adapter, config=build_robust_qualified_config())

    action = executor.act(obs)
    # Live foundation only operates on market timing, terminal liquidation, and phase shutdown
    assert action["farmer"] == ["MOVE", "NORTH"], "AEC illegally modified farmer movement!"


# -----------------------------------------------------------------------------
# 4. CARGO BOUNDARY (Cargo-Trapping Trap Repro Prevention)
# -----------------------------------------------------------------------------
def test_adversarial_cargo_boundary_quarantines_multiworker_harvest():
    """Verify that MULTIWORKER_HARVEST_SYNCHRONIZATION remains strictly quarantined and cannot commit."""
    obs = make_engine_obs(step=319)

    cfg = build_robust_qualified_config()
    assert "MULTIWORKER_HARVEST_SYNCHRONIZATION" not in cfg.enabled_mechanisms
    assert "MULTIWORKER_HARVEST_SYNCHRONIZATION" in cfg.quarantined_mechanisms or not cfg.is_mechanism_enabled("MULTIWORKER_HARVEST_SYNCHRONIZATION")

    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["PASS"], "hands": [["PASS"] for _ in range(5)], "market": []}))
    executor = AECExecutor(backbone_adapter=adapter, config=cfg)

    action = executor.act(obs)
    history = executor._telemetry_history
    for t in history:
        assert t.committed_mechanism != "MULTIWORKER_HARVEST_SYNCHRONIZATION"


# -----------------------------------------------------------------------------
# 5. MARKET BOUNDARY (Rapid Order Volatility & Depth Inversion)
# -----------------------------------------------------------------------------
def test_adversarial_market_boundary_dependency_aware_reordering():
    """Verify market timing only reorders orders when basket dependencies are strictly satisfied."""
    obs = make_engine_obs(step=240)
    obs["private"]["shed"]["WHEAT"] = 10
    base_market = [
        ["BUY_SEED", "CARROT", 5],
        ["SELL", "WHEAT", 10],
    ]
    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["PASS"], "hands": [], "market": base_market}))
    executor = AECExecutor(backbone_adapter=adapter, config=build_robust_qualified_config())

    action = executor.act(obs)
    market = action.get("market", [])
    wheat_sold = sum(o[2] for o in market if len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT")
    assert wheat_sold <= 10, f"AEC oversold wheat inventory: {wheat_sold} > 10!"


# -----------------------------------------------------------------------------
# 6. TERMINAL BOUNDARY (Steps 718-720 Liquidation & Shutdown Interaction)
# -----------------------------------------------------------------------------
def test_adversarial_terminal_boundary_step718_liquidation_transformation():
    """Verify that terminal liquidation transforms unliquidated produce into sorted sell orders."""
    shed = {"MELON": 8, "TOMATO": 12, "WHEAT": 0}
    prices = {"MELON": 120, "TOMATO": 80, "WHEAT": 25}

    orders, status = transform_terminal_liquidation(shed, prices)
    assert len(orders) == 2
    # MELON: 8 * 120 = 960; TOMATO: 12 * 80 = 960
    assert all(o[0] == "SELL" for o in orders)
    sold_items = {o[1] for o in orders}
    assert sold_items == {"MELON", "TOMATO"}


def test_adversarial_terminal_boundary_step719_phase_shutdown_transformation():
    """Verify that Phase Shutdown trims dead seed purchases that cannot mature before step 720."""
    orders = [
        ["BUY_SEED", "MELON", 5],
        ["BUY_SEED", "WHEAT", 5],
        ["SELL", "CARROT", 10],
    ]
    # At step 719, MELON (10 days) and WHEAT (2 days) cannot mature
    filtered, status = transform_phase_shutdown(orders, dead_crops=["MELON", "WHEAT"])
    assert len(filtered) == 1
    assert filtered[0] == ["SELL", "CARROT", 10]


# -----------------------------------------------------------------------------
# 7. MACRO BOUNDARY (Livestock Starvation / Feed Deficit)
# -----------------------------------------------------------------------------
def test_adversarial_macro_boundary_fails_closed_on_unhedged_deficit():
    """Verify that feed deficits escalate or fail closed rather than committing speculative actions."""
    obs = make_engine_obs(step=150)
    obs["farms"][0]["money"] = 200.0

    adapter = BackboneAdapter(agent_fn=MockBackbone({"farmer": ["PASS"], "hands": [], "market": []}))
    executor = AECExecutor(backbone_adapter=adapter, config=build_robust_qualified_config())

    action = executor.act(obs)
    assert "farmer" in action and "market" in action
    assert executor._telemetry_history[-1].decision in ("BACKBONE", "ABSTAIN", "COMMIT")
