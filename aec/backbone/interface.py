# SPDX-License-Identifier: MIT
"""Formal Backbone Interface & Continuation Policy Contracts (V26, §3, §4)."""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BaselineResult:
    """Immutable canonical snapshot of the backbone output for one step."""
    step: int
    action: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical_action_copy(self) -> Dict[str, Any]:
        """Return a deep copy of the baseline action for candidate mutation."""
        return copy.deepcopy(self.action)


class ContinuationPolicy(ABC):
    """Encapsulates isolated stateful continuation for shadow counterfactual rollouts."""

    @abstractmethod
    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        """Produce the next action for a simulated forward rollout state.

        Args:
            rollout: ShadowRolloutState representing simulated environment state.
            player: 0 or 1.

        Returns:
            Kaggle-compliant action dict {'farmer': [...], 'hands': [...], 'market': [...]}.
        """
        ...

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Capture isolated snapshot of continuation state."""
        ...

    @abstractmethod
    def restore(self, snap: Dict[str, Any]) -> None:
        """Restore continuation state exactly to snapshot."""
        ...


class BackbonePolicy(ABC):
    """Formal interface separating the macro-planning backbone from the AEC supervisor."""

    def call_once(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> BaselineResult:
        """Execute normal live action and wrap in a BaselineResult snapshot."""
        step = int(observation.get("step", 0) or 0)
        action = self.act(observation, configuration)
        return BaselineResult(step=step, action=action)

    @abstractmethod
    def identity(self) -> str:
        """Return canonical backbone name (e.g. 'V3_STANDALONE', 'V25_P3_UNIFIED')."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return version string."""
        ...

    @abstractmethod
    def code_hash(self) -> str:
        """Return SHA-256 fingerprint of the backbone implementation."""
        ...

    @abstractmethod
    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute normal live action for the active game step.

        Hard Invariant: Must be called exactly once per live game step.
        """
        ...

    @abstractmethod
    def macro_fingerprint(
        self,
        observation: Dict[str, Any],
        player: int = 0
    ) -> Dict[str, Any]:
        """Compute the macro economic fingerprint for regime divergence detection.

        Fields: cash, crop inventory, livestock count, worker count,
        planned crop cycle, market regime, terminal phase.
        """
        ...

    @abstractmethod
    def snapshot_state(self) -> Dict[str, Any]:
        """Capture a complete, isolated memory snapshot of the backbone state."""
        ...

    @abstractmethod
    def restore_state(self, snapshot: Dict[str, Any]) -> None:
        """Restore backbone state exactly from snapshot without side-effects."""
        ...

    @abstractmethod
    def create_continuation_policy(self) -> ContinuationPolicy:
        """Instantiate an isolated continuation policy for counterfactual exploration.

        Hard Invariant: Calls to the returned ContinuationPolicy must NEVER mutate
        or contaminate the live BackbonePolicy state.
        """
        ...

    @abstractmethod
    def get_future_trajectory(
        self,
        step: int,
        horizon: int,
        player: int = 0,
        n_hands: int = 0
    ) -> List[Dict[str, Any]]:
        """Extract deterministic planned actions for steps [step + 1 .. step + horizon - 1].

        Read-only lookahead for static plan alignment.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset state for a fresh match."""
        ...
