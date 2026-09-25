# SPDX-License-Identifier: MIT
"""HMEH Fallback System Layer.

Provides structured fallback regimes (NORMAL, CAUTION, RECOVERY, LIQUIDATION)
and an emergency hard fallback to protected A7 standalone execution.
"""

from __future__ import annotations
import importlib.util
import os
import sys
from typing import Any, Dict, Optional

_A7_AGENT = None


def load_fresh_a7():
    """Returns a completely isolated, fresh instance of the A7 standalone agent."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(repo_root, "candidates", "v30_a7_standalone", "main.py")
    if os.path.exists(path):
        import uuid
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        ns = {"__name__": f"v30_a7_iso_{uuid.uuid4().hex[:8]}"}
        exec(compile(code, path, "exec"), ns)
        return ns.get("agent")
    return None


def _load_a7_standalone():
    return load_fresh_a7()


class FallbackManager:
    def __init__(self):
        self.state = "NORMAL"
        self.consecutive_stalls = 0
        self.fallback_history: list = []
        
    def evaluate_transition(
        self,
        current_state: str,
        cash: float,
        runway_days: float,
        step: int,
        action_failed: bool = False
    ) -> str:
        """Determines the operational fallback regime."""
        if action_failed:
            self.consecutive_stalls += 1
        else:
            self.consecutive_stalls = 0
            
        if step >= 712:
            next_state = "LIQUIDATION"
        elif self.consecutive_stalls >= 3:
            next_state = "RECOVERY"
        elif runway_days < 2.0 or cash < 30.0:
            next_state = "CAUTION"
        else:
            next_state = "NORMAL"
            
        if next_state != self.state:
            self.fallback_history.append({
                "step": step,
                "from": self.state,
                "to": next_state,
                "cash": cash,
                "runway": runway_days,
                "stalls": self.consecutive_stalls
            })
            self.state = next_state
            
        return self.state

    def emergency_a7_fallback(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Emergency safe fallback: invokes the protected A7 standalone agent."""
        try:
            a7 = _load_a7_standalone()
            if a7 is not None:
                return a7(observation, configuration)
        except Exception:
            pass
        # Absolute minimal safe action
        hands = len((observation.get("farms") or [{}])[int(observation.get("player", 0) or 0)].get("hands", []))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hands)],
            "market": []
        }
