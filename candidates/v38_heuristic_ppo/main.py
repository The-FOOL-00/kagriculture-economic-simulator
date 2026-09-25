# SPDX-License-Identifier: MIT
"""Kagriculture V38 Heuristic-Guided Residual Policy Candidate Agent.

Architecture:
1. High-level economic state abstraction from legal observations.
2. Evaluates base action from V38 deterministic expert (V35 opening + A7 chassis).
3. Evaluates discrete macro option via residual actor-critic network.
4. Fail-closed safety enforcer validates liquidity, cooldowns, and bounds.
5. Deterministic executor executes approved option; falls back safely to heuristic on error.
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, Optional

_this_file = globals().get("__file__")
if _this_file:
    _candidate_dir = os.path.dirname(os.path.abspath(_this_file))
    REPO_ROOT = os.path.abspath(os.path.join(_candidate_dir, "..", ".."))
else:
    REPO_ROOT = os.path.abspath(".")
    _candidate_dir = os.path.join(REPO_ROOT, "candidates", "v38_heuristic_ppo")

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if _candidate_dir not in sys.path:
    sys.path.insert(0, _candidate_dir)

try:
    from evaluate import NeuralCandidateWrapper
    from config import SCRATCH_DIR
except ImportError:
    from candidates.v38_heuristic_ppo.evaluate import NeuralCandidateWrapper
    from candidates.v38_heuristic_ppo.config import SCRATCH_DIR

_PPO_CHECKPOINT = os.path.join(SCRATCH_DIR, "ppo_policy.pt")
_BC_CHECKPOINT = os.path.join(SCRATCH_DIR, "bc_policy.pt")

# Select best available checkpoint (PPO > BC > Pure Heuristic)
_ACTIVE_CHECKPOINT = _PPO_CHECKPOINT if os.path.exists(_PPO_CHECKPOINT) else (_BC_CHECKPOINT if os.path.exists(_BC_CHECKPOINT) else None)
_CANDIDATE = NeuralCandidateWrapper(checkpoint_path=_ACTIVE_CHECKPOINT, use_safety=True)


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant submission agent function."""
    global _CANDIDATE
    try:
        step = int(observation.get("step", 0) or 0)
        if step == 0:
            _CANDIDATE.reset()
        return _CANDIDATE.act(observation, configuration)
    except Exception:
        # Strict fail-closed fallback
        return _CANDIDATE.expert.get_base_action(observation, configuration)
