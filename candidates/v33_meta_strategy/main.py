# SPDX-License-Identifier: MIT
"""Kagriculture V33 Meta-Strategy Candidate Package.

Architecture:
- Low-Level Execution: Delegated entirely to verified expert routes (Default: R0_A7).
- High-Level Meta-Controller: Early-branch observable regime classifier (t in {24, 48, 72}).
- Gating: Confidence threshold, tail-risk constraint, one-switch-first policy.
- Fallback: Deterministic and instantaneous fallback to R0_A7 on any failure.
- Cryptographic verification of protected A7 incumbent on startup.
"""

from __future__ import annotations
import copy
import hashlib
import os
import sys
from typing import Any, Callable, Dict, Optional

# A7 Incumbent Protection Hash
A7_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from candidates.v33_meta_strategy.route_bank import RouteBank
from candidates.v33_meta_strategy.selector import RouteSelector

# Global singleton controllers for stateful match lifecycle
_BANK: Optional[RouteBank] = None
_SELECTOR: Optional[RouteSelector] = None
_A7_AGENT: Optional[Callable] = None
_TARGET_AGENT: Optional[Callable] = None


def _verify_incumbent():
    """Verifies that candidates/v30_a7_standalone/main.py has not been altered."""
    a7_path = os.path.join(_REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
    if os.path.exists(a7_path):
        with open(a7_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        if h != A7_SHA256:
            raise RuntimeError(f"A7 integrity violation! Expected {A7_SHA256}, got {h}")


def _init_system():
    global _BANK, _SELECTOR, _A7_AGENT, _TARGET_AGENT
    _verify_incumbent()
    if _BANK is None:
        _BANK = RouteBank()
        _A7_AGENT = _BANK.load_route("R0_A7")
        _TARGET_AGENT = _BANK.load_route("R2_DMITRII")
        _SELECTOR = RouteSelector(decision_steps=(24, 48, 72), min_gain_threshold=2500.0)


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Competition entrypoint conforming strictly to the Kaggle Environments specification."""
    global _BANK, _SELECTOR, _A7_AGENT, _TARGET_AGENT

    step = int(observation.get("step", 0) or 0)
    if step == 0 or _SELECTOR is None:
        _init_system()
        _SELECTOR.reset()

    # Early regime evaluation
    decision = _SELECTOR.evaluate(observation)

    # Route execution with automatic fallback
    if _SELECTOR.current_route == "R2_DMITRII" and _TARGET_AGENT is not None:
        try:
            return _TARGET_AGENT(observation, configuration)
        except Exception:
            # Revert to A7 default
            return _A7_AGENT(observation, configuration)

    return _A7_AGENT(observation, configuration)


if __name__ == "__main__":
    _init_system()
    print("V33 Meta Strategy Agent initialized and verified successfully!")
