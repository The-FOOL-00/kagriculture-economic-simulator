# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Telemetry & Residual Decision Contract.

Defines the ResidualDecision dataclass and structured match logging.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResidualDecision:
    """The formal contract for any P10 residual override."""
    step: int
    active: bool = False
    trigger_id: str = "NONE"
    trigger_reason: str = "A7_BASELINE_DEFAULT"
    base_action: Dict[str, Any] = field(default_factory=lambda: {"farmer": ["PASS"], "hands": [], "market": []})
    candidate_action: Dict[str, Any] = field(default_factory=lambda: {"farmer": ["PASS"], "hands": [], "market": []})
    counterfactual_score: float = 0.0
    baseline_score: float = 0.0
    paired_delta: float = 0.0
    worst_case_delta: float = 0.0
    confidence: float = 1.0
    legality_status: bool = True
    expiry_step: int = -1
    fallback_action: Dict[str, Any] = field(default_factory=lambda: {"farmer": ["PASS"], "hands": [], "market": []})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class P10TelemetryLogger:
    """Logs match-level events, decisions, and diagnostics."""
    def __init__(self):
        self.decisions: List[ResidualDecision] = []
        self.total_steps: int = 0
        self.total_overrides: int = 0
        self.total_rejected: int = 0
        self.total_fallbacks: int = 0

    def record_decision(self, dec: ResidualDecision):
        self.decisions.append(dec)
        self.total_steps += 1
        if dec.active:
            self.total_overrides += 1

    def summary(self) -> Dict[str, Any]:
        return {
            "total_steps": self.total_steps,
            "total_overrides": self.total_overrides,
            "override_rate": self.total_overrides / max(1, self.total_steps),
            "total_rejected": self.total_rejected,
            "total_fallbacks": self.total_fallbacks
        }
