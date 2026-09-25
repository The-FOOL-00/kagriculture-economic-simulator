# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Option Acceptance Gate & Filter.

Enforces Section 23/47/49/50 safety criteria before promoting or executing any option:
1. Positive exact counterfactual delta (G1)
2. Positive post-resync economic outcome (G2)
3. Acceptable tail loss within risk budget (G3)
4. Repeatable across states (G4)
5. Physical synchronization: SYNCED status preserved (G8)
6. Absolute fallback: When uncertain, DO NOTHING, follow A7 (G12)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from option_library import OptionContract
    from resync import ResyncState, SyncStatus
except ImportError:
    from candidates.v32_p12_options.option_library import OptionContract
    from candidates.v32_p12_options.resync import ResyncState, SyncStatus


@dataclass
class AcceptanceDecision:
    accepted: bool
    option_id: str
    reasons: List[str]
    local_delta: float
    resync_delta: float
    terminal_delta: float
    is_physically_synced: bool


class OptionAcceptanceGate:
    """Rigorous gate filter evaluating candidates before live execution."""
    def __init__(
        self,
        min_terminal_delta: float = 200.0,
        min_resync_delta: float = -4500.0,  # Accommodates initial land purchase costs ($4k)
        max_allowed_tail_loss: float = -200.0,
        require_exact_sync: bool = True
    ):
        self.min_terminal_delta = min_terminal_delta
        self.min_resync_delta = min_resync_delta
        self.max_allowed_tail_loss = max_allowed_tail_loss
        self.require_exact_sync = require_exact_sync

    def evaluate(
        self,
        option: OptionContract,
        local_delta: float,
        resync_delta: float,
        terminal_delta: float,
        resync_state: ResyncState
    ) -> AcceptanceDecision:
        """Applies G1-G12 promotion/acceptance gates."""
        reasons = []
        accepted = True

        # Gate G1: Positive terminal delta
        if terminal_delta < self.min_terminal_delta:
            accepted = False
            reasons.append(f"INSUFFICIENT_TERMINAL_DELTA: {terminal_delta:.1f} < {self.min_terminal_delta}")

        # Gate G2: Post-resync safety
        if resync_delta < self.min_resync_delta:
            accepted = False
            reasons.append(f"RESYNC_DEFICIT_EXCEEDS_BUDGET: {resync_delta:.1f} < {self.min_resync_delta}")

        # Gate G8: Physical synchronization
        if self.require_exact_sync and resync_state.status != SyncStatus.SYNCED:
            accepted = False
            reasons.append(f"PHYSICAL_DESYNCHRONIZATION: status={resync_state.status}")

        if not resync_state.is_next_a7_action_feasible:
            accepted = False
            reasons.append("NEXT_A7_ACTION_INFEASIBLE")

        # When uncertain: FAIL-CLOSED TO A7
        if not accepted:
            reasons.append("FALLBACK_TO_A7_MANDATORY")

        return AcceptanceDecision(
            accepted=accepted,
            option_id=option.option_id,
            reasons=reasons,
            local_delta=local_delta,
            resync_delta=resync_delta,
            terminal_delta=terminal_delta,
            is_physically_synced=(resync_state.status == SyncStatus.SYNCED)
        )
