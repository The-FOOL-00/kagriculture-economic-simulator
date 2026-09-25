# SPDX-License-Identifier: MIT
"""
Telemetry Logger for Phase 11 Terminal Physical Search.
Records detailed telemetry for every terminal decision and activation attempt.
"""
import time
from typing import Dict, Any, List, Optional

class TerminalTelemetry:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.total_search_time: float = 0.0
        self.evaluations_count: int = 0
        self.activations_count: int = 0

    def record_decision(
        self,
        step: int,
        a7_action: Dict[str, Any],
        candidate_action: Optional[Dict[str, Any]],
        accepted: bool,
        reason: str,
        delta: float,
        baseline_val: float,
        candidate_val: float,
        budget: int,
        search_duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        event = {
            "step": step,
            "accepted": accepted,
            "reason": reason,
            "delta": delta,
            "baseline_val": baseline_val,
            "candidate_val": candidate_val,
            "budget": budget,
            "search_time_ms": search_duration * 1000.0,
            "metadata": metadata or {}
        }
        self.events.append(event)
        self.evaluations_count += 1
        self.total_search_time += search_duration
        if accepted:
            self.activations_count += 1

    def summary(self) -> Dict[str, Any]:
        return {
            "evaluations": self.evaluations_count,
            "activations": self.activations_count,
            "total_search_time_s": self.total_search_time,
            "mean_search_time_ms": (self.total_search_time / max(1, self.evaluations_count)) * 1000.0,
            "events": self.events
        }
