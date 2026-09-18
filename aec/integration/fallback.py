# SPDX-License-Identifier: MIT
"""Robust Fallback Layer and Telemetry Policy (§11)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class FallbackReason(str, Enum):
    """Explicit, inspectable reasons for reverting to the V3 baseline chassis (§11)."""
    CANDIDATE_UNCERTAIN = "CANDIDATE_UNCERTAIN"
    COUNTERFACTUAL_UNAVAILABLE = "COUNTERFACTUAL_UNAVAILABLE"
    OPPONENT_MODEL_UNCLEAR = "OPPONENT_MODEL_UNCLEAR"
    DEPENDENCY_CLOSURE_INCOMPLETE = "DEPENDENCY_CLOSURE_INCOMPLETE"
    PATCH_STALE = "PATCH_STALE"
    RUNTIME_BUDGET_EXCEEDED = "RUNTIME_BUDGET_EXCEEDED"
    SAFETY_INVARIANT_VIOLATED = "SAFETY_INVARIANT_VIOLATED"
    ECONOMICALLY_INFERIOR = "ECONOMICALLY_INFERIOR"
    SCIENTIFIC_QUARANTINE = "SCIENTIFIC_QUARANTINE"
    BACKBONE_INVOCATION_EXCEPTION = "BACKBONE_INVOCATION_EXCEPTION"
    NO_FEASIBLE_CANDIDATE = "NO_FEASIBLE_CANDIDATE"


@dataclass
class FallbackRecord:
    """Detailed audit record of an individual fallback event (§11)."""
    step: int
    reason: FallbackReason
    candidate_id: Optional[str]
    mechanism_family: Optional[str]
    time_saved_ms: float
    candidate_failed: bool
    baseline_action: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "reason": self.reason.value,
            "candidate_id": self.candidate_id,
            "family": self.mechanism_family,
            "time_saved_ms": round(self.time_saved_ms, 2),
            "candidate_failed": self.candidate_failed,
            "rationale": self.rationale,
        }


class RobustFallbackPolicy:
    """Enforces deterministic, fail-closed fallback to the strong V3 chassis (§11).
    
    Whenever any uncertainty, budget overflow, or invariant failure arises:
    AEC returns cleanly to baseline, recording full telemetry without guessing.
    """

    def __init__(self) -> None:
        self._history: List[FallbackRecord] = []

    def record_fallback(
        self,
        step: int,
        reason: FallbackReason,
        baseline_action: Dict[str, Any],
        candidate_id: Optional[str] = None,
        mechanism_family: Optional[str] = None,
        time_saved_ms: float = 0.0,
        candidate_failed: bool = True,
        rationale: str = ""
    ) -> FallbackRecord:
        """Create and log a formal fallback record."""
        rec = FallbackRecord(
            step=step,
            reason=reason,
            candidate_id=candidate_id,
            mechanism_family=mechanism_family,
            time_saved_ms=time_saved_ms,
            candidate_failed=candidate_failed,
            baseline_action=copy.deepcopy(baseline_action),
            rationale=rationale,
        )
        self._history.append(rec)
        return rec

    @property
    def fallback_count(self) -> int:
        """Total fallback invocations across lifetime."""
        return len(self._history)

    def get_count_by_reason(self) -> Dict[str, int]:
        """Aggregate breakdown of fallback counts by reason."""
        counts: Dict[str, int] = {}
        for r in self._history:
            counts[r.reason.value] = counts.get(r.reason.value, 0) + 1
        return counts

    def get_total_time_saved_ms(self) -> float:
        """Total cumulative simulation time saved by early fallback."""
        return sum(r.time_saved_ms for r in self._history)

    def get_latest_record(self) -> Optional[FallbackRecord]:
        return self._history[-1] if self._history else None

    def get_history(self) -> List[FallbackRecord]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
