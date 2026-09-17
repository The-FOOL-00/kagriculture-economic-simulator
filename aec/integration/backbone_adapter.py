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
        v3_callable: Optional[Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]] = None,
        continuation_provider: Optional[Callable[[int, int, int, int], List[Dict[str, Any]]]] = None
    ) -> None:
        self.config = config or AECConfig()
        self._agent_fn = agent_fn or v3_callable
        self._continuation_provider = continuation_provider
        self._v3_chassis: Any = None
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
        # Extract underlying Chassis for read-only route tape lookahead
        impl = ns.get("_PARENT_NS", {}).get("_IMPL", None)
        if impl is not None:
            self._v3_chassis = getattr(impl, "chassis", None)

    @staticmethod
    def _align_hands(action: Dict[str, Any], n_hands: int) -> Dict[str, Any]:
        """Ensure hand count matches live farm topology."""
        act = copy.deepcopy(action)
        hands = act.get("hands", []) or []
        if not isinstance(hands, list):
            hands = []
        if len(hands) < n_hands:
            hands = hands + [["PASS"] for _ in range(n_hands - len(hands))]
        elif len(hands) > n_hands:
            hands = hands[:n_hands]
        act["hands"] = hands
        act.setdefault("farmer", ["PASS"])
        act.setdefault("market", [])
        return act

    def get_future_trajectory(
        self,
        step: int,
        horizon: int,
        player: int = 0,
        n_hands: int = 0
    ) -> List[Dict[str, Any]]:
        """Extract deterministic planned backbone actions for future steps (step+1 .. step+horizon-1).
        
        Hard Invariants:
        1. Never invokes the live backbone agent.
        2. Never mutates live state, ledgers, or chassis.
        3. Completely read-only lookup from the pre-computed route tape or continuation provider.
        """
        if horizon <= 1:
            return []

        # 1. Custom continuation provider if explicitly supplied
        if self._continuation_provider is not None:
            return self._continuation_provider(step, horizon, player, n_hands)

        # 2. Frozen V3 Chassis extraction
        chassis = self._v3_chassis or getattr(self._agent_fn, "chassis", None)
        if chassis is not None and hasattr(chassis, "routes"):
            players = getattr(chassis, "players", {})
            native = players.get(player) if isinstance(players, dict) else None
            route_id = 2 if step >= 648 else (native or {}).get("route")
            if route_id is None:
                route_id = 0
            
            routes = getattr(chassis, "routes", {})
            tape = routes.get(route_id, [])
            trajectory: List[Dict[str, Any]] = []
            for offset in range(1, horizon):
                future_step = step + offset
                if 0 <= future_step < len(tape) and isinstance(tape[future_step], dict):
                    act = self._align_hands(tape[future_step], n_hands)
                    trajectory.append(act)
                else:
                    trajectory.append({
                        "farmer": ["PASS"],
                        "hands": [["PASS"] for _ in range(n_hands)],
                        "market": []
                    })
            return trajectory

        # 3. If mock/agent has schedule or routes attribute
        if hasattr(self._agent_fn, "schedule"):
            schedule = getattr(self._agent_fn, "schedule")
            trajectory = []
            for offset in range(1, horizon):
                future_step = step + offset
                if 0 <= future_step < len(schedule) and isinstance(schedule[future_step], dict):
                    trajectory.append(self._align_hands(schedule[future_step], n_hands))
                else:
                    trajectory.append({
                        "farmer": ["PASS"],
                        "hands": [["PASS"] for _ in range(n_hands)],
                        "market": []
                    })
            return trajectory

        if hasattr(self._agent_fn, "routes"):
            routes = getattr(self._agent_fn, "routes")
            tape = routes.get(0, []) if isinstance(routes, dict) else routes
            trajectory = []
            for offset in range(1, horizon):
                future_step = step + offset
                if 0 <= future_step < len(tape) and isinstance(tape[future_step], dict):
                    trajectory.append(self._align_hands(tape[future_step], n_hands))
                else:
                    trajectory.append({
                        "farmer": ["PASS"],
                        "hands": [["PASS"] for _ in range(n_hands)],
                        "market": []
                    })
            return trajectory

        # 4. Fallback for simple callable mocks with no future schedule:
        # Repeat the cached baseline action padded with aligned hands
        if self._cached_result is not None:
            base_act = self._align_hands(self._cached_result.action, n_hands)
            return [copy.deepcopy(base_act) for _ in range(horizon - 1)]

        return [{
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(n_hands)],
            "market": []
        } for _ in range(horizon - 1)]

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
