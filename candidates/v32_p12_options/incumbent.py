# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Incumbent Interface.

Provides read-only, verified access to the protected incumbent A7 agent
(candidates/v30_a7_standalone/main.py). Guarantees SHA-256 integrity and
bit-identical baseline execution.
"""

from __future__ import annotations
import copy
import hashlib
import os
import sys
from typing import Any, Dict, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

A7_RELATIVE_PATH = "candidates/v30_a7_standalone/main.py"
A7_ABSOLUTE_PATH = os.path.join(REPO_ROOT, A7_RELATIVE_PATH)
EXPECTED_A7_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"


def verify_a7_integrity(path: Optional[str] = None) -> bool:
    """Computes SHA-256 of the A7 standalone agent and verifies against expected hash."""
    target_path = path or A7_ABSOLUTE_PATH
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"A7 standalone agent not found at {target_path}")
    h = hashlib.sha256()
    with open(target_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    actual_hash = h.hexdigest().lower()
    if actual_hash != EXPECTED_A7_SHA256.lower():
        raise RuntimeError(
            f"A7 INTEGRITY BREACH: expected {EXPECTED_A7_SHA256}, got {actual_hash}"
        )
    return True


class A7Incumbent:
    """Encapsulates the protected A7 agent."""
    def __init__(self):
        verify_a7_integrity()
        from scripts.v32_common import load_agent
        self._agent = load_agent("E9_AST")
        self._step = 0

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates bit-identical A7 action."""
        action = self._agent.act(observation, configuration)
        return copy.deepcopy(action)

    def reset(self):
        """Constructs a fresh instance for a new match."""
        from scripts.v32_common import load_agent
        self._agent = load_agent("E9_AST")
        self._step = 0
