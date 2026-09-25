# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Telemetry & Diagnostic Logging.

Structured JSONL telemetry for tracking option opportunities, search decisions,
resynchronization status, and match economic accounting.
"""

from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List, Optional


class P12TelemetryLogger:
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self.events: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, data: Dict[str, Any]):
        record = {
            "timestamp": time.time(),
            "event_type": event_type,
            **data
        }
        self.events.append(record)
        if self.log_path:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def log_detection(self, step: int, detected: bool, candidates: List[str], reasons: List[str]):
        self.log_event("DETECTION", {
            "step": step,
            "detected": detected,
            "candidates": candidates,
            "reasons": reasons
        })

    def log_acceptance(self, step: int, option_id: str, accepted: bool, deltas: Dict[str, float], reasons: List[str]):
        self.log_event("ACCEPTANCE", {
            "step": step,
            "option_id": option_id,
            "accepted": accepted,
            "deltas": deltas,
            "reasons": reasons
        })

    def log_option_execution(self, step: int, option_id: str, action_taken: int, tick: int, status: str):
        self.log_event("EXECUTION_TICK", {
            "step": step,
            "option_id": option_id,
            "action_taken": action_taken,
            "tick": tick,
            "status": status
        })

    def log_resync_check(self, step: int, resync_status: str, displacement: int, state_distance: float):
        self.log_event("RESYNC_CHECK", {
            "step": step,
            "status": resync_status,
            "displacement": displacement,
            "state_distance": state_distance
        })
