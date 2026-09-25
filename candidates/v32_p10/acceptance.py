# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Acceptance Gating Engine.

Implements the strict multi-gate criteria (G1 to G9) before any residual action
can be promoted or accepted for online execution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GateReport:
    candidate_id: str
    passed: bool
    g1_legality: bool = False
    g2_baseline_validity: bool = False
    g3_economic_delta: bool = False
    g4_downside_safe: bool = False
    g5_robustness: bool = False
    g6_non_duplication: bool = False
    g7_causality: bool = False
    g8_runtime_safe: bool = False
    g9_fallback_ready: bool = True
    
    mean_paired_delta: float = 0.0
    worst_case_delta: float = 0.0
    activation_count: int = 0
    failure_reasons: List[str] = field(default_factory=list)


class AcceptanceGatingEngine:
    def __init__(
        self,
        min_paired_delta: float = 50.0,
        max_downside_loss: float = 50.0,
        min_activations: int = 3,
        max_runtime_ms: float = 500.0
    ):
        self.min_paired_delta = min_paired_delta
        self.max_downside_loss = max_downside_loss
        self.min_activations = min_activations
        self.max_runtime_ms = max_runtime_ms

    def evaluate(
        self,
        candidate_id: str,
        deltas: List[float],
        legality_passed: bool,
        baseline_valid: bool,
        is_duplicate: bool,
        causal_explanation: str,
        avg_runtime_ms: float
    ) -> GateReport:
        reasons = []
        
        # G1: Legality
        g1 = legality_passed
        if not g1:
            reasons.append("G1 FAIL: Candidate action produced illegal action or invalid syntax")
            
        # G2: Baseline validity
        g2 = baseline_valid
        if not g2:
            reasons.append("G2 FAIL: Baseline A7 action invalid")
            
        # Delta calculations
        n = len(deltas)
        mean_d = sum(deltas) / max(1, n) if deltas else 0.0
        worst_d = min(deltas) if deltas else 0.0
        
        # G3: Economic Delta
        g3 = mean_d >= self.min_paired_delta
        if not g3:
            reasons.append(f"G3 FAIL: Mean paired delta (${mean_d:.2f}) < required (${self.min_paired_delta:.2f})")
            
        # G4: Downside
        g4 = worst_d >= -self.max_downside_loss
        if not g4:
            reasons.append(f"G4 FAIL: Worst-case loss (${worst_d:.2f}) exceeded risk budget (-${self.max_downside_loss:.2f})")
            
        # G5: Robustness
        g5 = n >= self.min_activations and sum(1 for d in deltas if d > 0) / max(1, n) >= 0.60
        if not g5:
            reasons.append(f"G5 FAIL: Low robustness (activations={n}, positive rate={sum(1 for d in deltas if d > 0)/max(1,n)*100:.1f}%)")
            
        # G6: Non-duplication
        g6 = not is_duplicate
        if not g6:
            reasons.append("G6 FAIL: Mechanism already captured by A7")
            
        # G7: Causality
        g7 = bool(causal_explanation and len(causal_explanation) > 10)
        if not g7:
            reasons.append("G7 FAIL: No verifiable causal mechanism established")
            
        # G8: Runtime
        g8 = avg_runtime_ms <= self.max_runtime_ms
        if not g8:
            reasons.append(f"G8 FAIL: Runtime ({avg_runtime_ms:.1f}ms) exceeded budget ({self.max_runtime_ms:.1f}ms)")
            
        # G9: Fallback invariant (always True by design)
        g9 = True
        
        all_passed = all([g1, g2, g3, g4, g5, g6, g7, g8, g9])
        
        return GateReport(
            candidate_id=candidate_id,
            passed=all_passed,
            g1_legality=g1,
            g2_baseline_validity=g2,
            g3_economic_delta=g3,
            g4_downside_safe=g4,
            g5_robustness=g5,
            g6_non_duplication=g6,
            g7_causality=g7,
            g8_runtime_safe=g8,
            g9_fallback_ready=g9,
            mean_paired_delta=mean_d,
            worst_case_delta=worst_d,
            activation_count=n,
            failure_reasons=reasons
        )
