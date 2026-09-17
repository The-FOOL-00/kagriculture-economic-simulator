# SPDX-License-Identifier: MIT
"""AEC Backbone Adapter (§5, §19, Correction 0.6, Correction 0.7)."""

from __future__ import annotations

import copy
import hashlib
import os
import tarfile
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from aec.config import AECConfig


@dataclass(frozen=True)
class BaselineResult:
    """Immutable canonical snapshot of the backbone output for one step."""
    step: int
    action: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical_action_copy(self) -> Dict[str, Any]:
        """Return a deep copy of the baseline action for candidate mutation."""
        return copy.deepcopy(self.action)


class BackboneAdapter:
    """Isolates the backbone agent and enforces the EXACTLY-ONE-LIVE-CALL invariant.
    
    Hard Invariants:
    1. Exactly one live call per game step. Repeated calls raise RuntimeError.
    2. The live baseline action is stored in an immutable snapshot.
    3. The underlying backbone state is never called during shadow search.
    """

    def __init__(
        self,
        agent_fn: Optional[Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]] = None,
        config: Optional[AECConfig] = None,
        v3_callable: Optional[Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]] = None
    ) -> None:
        self.config = config or AECConfig()
        self._agent_fn = agent_fn or v3_callable
        self._last_called_step: int = -1
        self._cached_result: Optional[BaselineResult] = None
        self._call_count: int = 0

        # If no explicit agent_fn provided, load V3 frozen from tarball
        if self._agent_fn is None:
            self._load_frozen_v3()

    def _load_frozen_v3(self) -> None:
        """Load frozen V3 implementation directly from immutable tarball in memory."""
        tar_path = self.config.v3_tarball_path
        if not os.path.isabs(tar_path):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            tar_path = os.path.join(repo_root, tar_path)

        if not os.path.exists(tar_path):
            raise FileNotFoundError(f"V3 frozen submission tarball missing: {tar_path}")

        # Verify SHA-256 before loading
        with open(tar_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != self.config.v3_tarball_sha256:
            raise RuntimeError(
                f"AEC FAIL-CLOSED: V3 tarball SHA256 mismatch!\n"
                f"Expected: {self.config.v3_tarball_sha256}\n"
                f"Got:      {digest}"
            )

        with tarfile.open(tar_path, "r:gz") as tar:
            main_member = tar.extractfile("main.py")
            if main_member is None:
                raise RuntimeError("Failed to extract main.py from V3 tarball")
            v3_code = main_member.read().decode("utf-8")

        ns: Dict[str, Any] = {"__name__": "aec_v3_frozen_runtime"}
        exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
        agent_callable = ns.get("agent")
        if not callable(agent_callable):
            raise RuntimeError("V3 frozen main.py does not define callable 'agent'")

        self._agent_fn = agent_callable

    def call_once(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> BaselineResult:
        """Call the live backbone agent exactly once for the current turn.
        
        Raises RuntimeError if called twice for the same step.
        """
        step = int(observation.get("step", 0) or 0)

        # Enforce exactly one call per step
        if step == self._last_called_step and self._cached_result is not None:
            raise RuntimeError(
                f"CRITICAL AEC INVARIANT BREACH: Baseline agent invoked twice for step {step}! "
                f"AEC mandates exactly one live call per step."
            )

        assert self._agent_fn is not None
        raw_action = self._agent_fn(observation, configuration)
        self._call_count += 1
        self._last_called_step = step

        # Canonical immutable snapshot
        canonical_action = copy.deepcopy(raw_action)
        self._cached_result = BaselineResult(
            step=step,
            action=canonical_action,
            metadata={"call_count": self._call_count}
        )
        return self._cached_result

    @property
    def total_calls(self) -> int:
        return self._call_count

    def get_cached_result(self) -> Optional[BaselineResult]:
        return self._cached_result

    def reset_for_new_game(self) -> None:
        self._last_called_step = -1
        self._cached_result = None
