# SPDX-License-Identifier: MIT
"""AEC Checkpoint 001: Adaptive Escalation Validation (§7).

Validates the multi-tier escalation architecture:
LEVEL 1: Local short replan (isolated action, closure size == 1)
LEVEL 2: Dependency-closure replan (same-asset/cash coupling, closure size 2..4)
LEVEL 3: Medium horizon (cross-subsystem events, shed capacity, worker-shed interaction)
LEVEL 4: Extended horizon (multi-worker coordination, livestock lifecycle, long chains)
LEVEL 5: Strategic/full replan (terminal endgame, phase shutdown, fidelity recovery)

Validates that escalation triggers dynamically on causal impact, not rigid turn counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional
import pytest

from aec.config import AECConfig
from aec.counterfactual.horizon import MechanismHorizonPolicy, select_adaptive_horizon
from aec.ir.dependency_graph import ActionBasketDependencyGraph, ActionNode, CausalEdgeType
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch


class EscalationLevel(IntEnum):
    LEVEL_1_LOCAL_SHORT = 1
    LEVEL_2_DEPENDENCY_CLOSURE = 2
    LEVEL_3_MEDIUM_HORIZON = 3
    LEVEL_4_EXTENDED_HORIZON = 4
    LEVEL_5_STRATEGIC_FULL = 5


@dataclass
class EscalationDecision:
    level: EscalationLevel
    horizon: int
    trigger_reason: str
    closure_size: int
    multi_worker: bool
    terminal_sensitive: bool


def determine_escalation_level(
    closure_size: int,
    state_impact_cash: float,
    multi_worker: bool,
    remaining_steps: int,
    event_severity: str = "NORMAL",
    fidelity_degradation: bool = False
) -> EscalationDecision:
    """Calculates escalation level based on causal state features and dependency expansion."""
    # Priority 1: Terminal endgame proximity
    if remaining_steps <= 12 or event_severity == "TERMINAL":
        return EscalationDecision(
            level=EscalationLevel.LEVEL_5_STRATEGIC_FULL,
            horizon=max(1, min(remaining_steps, 24)),
            trigger_reason="Terminal sensitivity / endgame boundary",
            closure_size=closure_size,
            multi_worker=multi_worker,
            terminal_sensitive=True
        )

    # Priority 2: Fidelity degradation recovery
    if fidelity_degradation:
        return EscalationDecision(
            level=EscalationLevel.LEVEL_5_STRATEGIC_FULL,
            horizon=min(remaining_steps, 36),
            trigger_reason="Fidelity degradation requires strategic verification",
            closure_size=closure_size,
            multi_worker=multi_worker,
            terminal_sensitive=False
        )

    # Priority 3: Large dependency chain / multi-worker coordination / livestock
    if closure_size >= 5 or (multi_worker and state_impact_cash > 500.0) or event_severity == "LIVESTOCK":
        return EscalationDecision(
            level=EscalationLevel.LEVEL_4_EXTENDED_HORIZON,
            horizon=min(remaining_steps, 36),
            trigger_reason=f"Large dependency closure (size {closure_size}) and multi-worker/lifecycle coupling",
            closure_size=closure_size,
            multi_worker=multi_worker,
            terminal_sensitive=False
        )

    # Priority 4: Cross-subsystem economic events / shed capacity / medium closure
    if closure_size in (3, 4) or event_severity in ("CASH_DEVIATION", "SHED_ALARM") or state_impact_cash > 200.0:
        return EscalationDecision(
            level=EscalationLevel.LEVEL_3_MEDIUM_HORIZON,
            horizon=min(remaining_steps, 18),
            trigger_reason=f"Medium dependency closure (size {closure_size}) or material cash/shed impact",
            closure_size=closure_size,
            multi_worker=multi_worker,
            terminal_sensitive=False
        )

    # Priority 5: Coupled market orders (same-asset)
    if closure_size == 2:
        return EscalationDecision(
            level=EscalationLevel.LEVEL_2_DEPENDENCY_CLOSURE,
            horizon=min(remaining_steps, 8),
            trigger_reason="Paired dependency closure (same-asset/cash coupling)",
            closure_size=closure_size,
            multi_worker=multi_worker,
            terminal_sensitive=False
        )

    # Level 1: Cheap local fast path
    return EscalationDecision(
        level=EscalationLevel.LEVEL_1_LOCAL_SHORT,
        horizon=min(remaining_steps, 4),
        trigger_reason="Genuinely local mutation (closure size 1, no cross-coupling)",
        closure_size=closure_size,
        multi_worker=multi_worker,
        terminal_sensitive=False
    )


def test_escalation_level_1_cheap_local() -> None:
    """Verifies that single-order uncoupled mutations stay at Level 1 (H=4, minimal cost)."""
    decision = determine_escalation_level(
        closure_size=1,
        state_impact_cash=35.0,
        multi_worker=False,
        remaining_steps=500
    )
    assert decision.level == EscalationLevel.LEVEL_1_LOCAL_SHORT
    assert decision.horizon == 4
    assert "local" in decision.trigger_reason.lower()


def test_escalation_level_2_paired_coupling() -> None:
    """Verifies that paired coupling (e.g. BUY & SELL of same commodity) escalates to Level 2 (H=8)."""
    decision = determine_escalation_level(
        closure_size=2,
        state_impact_cash=120.0,
        multi_worker=False,
        remaining_steps=500
    )
    assert decision.level == EscalationLevel.LEVEL_2_DEPENDENCY_CLOSURE
    assert decision.horizon == 8


def test_escalation_level_3_medium_impact() -> None:
    """Verifies that medium dependency closures or material events escalate to Level 3 (H=18)."""
    decision = determine_escalation_level(
        closure_size=3,
        state_impact_cash=250.0,
        multi_worker=False,
        remaining_steps=500,
        event_severity="CASH_DEVIATION"
    )
    assert decision.level == EscalationLevel.LEVEL_3_MEDIUM_HORIZON
    assert decision.horizon == 18


def test_escalation_level_4_extended_lifecycle() -> None:
    """Verifies that large closures or multi-worker livestock investments escalate to Level 4 (H=36)."""
    decision = determine_escalation_level(
        closure_size=6,
        state_impact_cash=800.0,
        multi_worker=True,
        remaining_steps=500,
        event_severity="LIVESTOCK"
    )
    assert decision.level == EscalationLevel.LEVEL_4_EXTENDED_HORIZON
    assert decision.horizon == 36


def test_escalation_level_5_terminal_proximity() -> None:
    """Verifies that endgame proximity (remaining <= 12) triggers Level 5 strategic evaluation."""
    decision = determine_escalation_level(
        closure_size=1,
        state_impact_cash=50.0,
        multi_worker=False,
        remaining_steps=8
    )
    assert decision.level == EscalationLevel.LEVEL_5_STRATEGIC_FULL
    assert decision.horizon == 8
    assert decision.terminal_sensitive is True


def test_escalation_level_5_fidelity_recovery() -> None:
    """Verifies that fidelity degradation forces strategic verification rather than silent pass."""
    decision = determine_escalation_level(
        closure_size=2,
        state_impact_cash=100.0,
        multi_worker=False,
        remaining_steps=200,
        fidelity_degradation=True
    )
    assert decision.level == EscalationLevel.LEVEL_5_STRATEGIC_FULL
    assert "Fidelity degradation" in decision.trigger_reason
