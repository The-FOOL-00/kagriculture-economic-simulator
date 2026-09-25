# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Incumbent Layer.

Loads and executes the frozen A7 incumbent agent in strict isolation.
Zero modifications to A7 source files.
"""

from __future__ import annotations
import copy
import os
import sys
import uuid
from typing import Any, Dict, Optional


def load_fresh_a7():
    """Loads a fresh, isolated callable instance of A7 standalone agent.
    
    Each call compiles and executes the frozen A7 standalone script in a unique
    namespace, ensuring clean internal chassis and route state per episode.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(repo_root, "candidates", "v30_a7_standalone", "main.py")
    if not os.path.exists(path):
        raise FileNotFoundError(f"A7 standalone file not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
        
    ns = {"__name__": f"v32_p10_a7_iso_{uuid.uuid4().hex[:8]}"}
    exec(compile(code, path, "exec"), ns)
    agent_fn = ns.get("agent")
    if not callable(agent_fn):
        raise RuntimeError("Failed to load callable agent from A7 standalone")
    return agent_fn


class A7Incumbent:
    """Manages the lifecycle of an isolated A7 agent instance."""
    def __init__(self):
        self._agent_fn = load_fresh_a7()
        
    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query the incumbent A7 policy."""
        try:
            action = self._agent_fn(observation, configuration)
            if not isinstance(action, dict):
                action = {"farmer": ["PASS"], "hands": [], "market": []}
            return copy.deepcopy(action)
        except Exception:
            # Conservative fallback
            hands = len((observation.get("farms") or [{}])[int(observation.get("player", 0) or 0)].get("hands", []))
            return {
                "farmer": ["PASS"],
                "hands": [["PASS"] for _ in range(hands)],
                "market": []
            }
