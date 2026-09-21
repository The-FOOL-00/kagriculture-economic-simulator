# SPDX-License-Identifier: MIT
"""V3 Backbone Adapter conforming to BackbonePolicy (§5)."""

from __future__ import annotations

import copy
import hashlib
import os
import tarfile
from typing import Any, Callable, Dict, List, Optional

from aec.backbone.interface import BackbonePolicy, ContinuationPolicy
from aec.backbone.utils import align_hands, build_simulated_observation, compute_base_macro_fingerprint
from aec.config import AECConfig


def snapshot_v3_globals(agent_fn: Any) -> Dict[str, Any]:
    """Capture a complete memory snapshot of V3 globals and chassis state."""
    snap: Dict[str, Any] = {"parent": {}}

    if hasattr(agent_fn, "chassis"):
        chassis = agent_fn.chassis
        if hasattr(chassis, "state"):
            snap["chassis_state"] = copy.deepcopy(chassis.state)
        if hasattr(chassis, "players"):
            snap["chassis_players"] = copy.deepcopy(chassis.players)

    if hasattr(agent_fn, "__globals__"):
        ns = agent_fn.__globals__
        p_ns = ns.get("_PARENT_NS", {})
        snap["TELEMETRY"] = copy.deepcopy(ns.get("TELEMETRY", {}))

        p_snap = snap["parent"]
        for k, v in p_ns.items():
            if k == "_IMPL" and hasattr(v, "chassis"):
                chassis = v.chassis
                p_snap["_IMPL_players"] = copy.deepcopy(getattr(chassis, "players", {}))
                p_snap["_IMPL_diag"] = copy.deepcopy(getattr(chassis, "diagnostics", {}))
            elif isinstance(v, dict) and any(
                k.endswith(s)
                for s in (
                    "_STATES", "_PLAYERS", "_HORIZONS", "_LAST", "_PREVIOUS",
                    "_PROBES", "_RESERVES", "_PENDING", "_REPORT", "_STATS"
                )
            ):
                p_snap[k] = copy.deepcopy(v)

    return snap


def restore_v3_globals(agent_fn: Any, snap: Dict[str, Any]) -> None:
    """Restore V3 globals and chassis state exactly from a snapshot."""
    if not snap:
        return

    if hasattr(agent_fn, "chassis"):
        chassis = agent_fn.chassis
        if "chassis_state" in snap and hasattr(chassis, "state"):
            chassis.state = copy.deepcopy(snap["chassis_state"])
        if "chassis_players" in snap and hasattr(chassis, "players"):
            chassis.players = copy.deepcopy(snap["chassis_players"])

    if hasattr(agent_fn, "__globals__"):
        ns = agent_fn.__globals__
        p_ns = ns.get("_PARENT_NS", {})

        if "TELEMETRY" in snap and "TELEMETRY" in ns:
            ns["TELEMETRY"].clear()
            ns["TELEMETRY"].update(copy.deepcopy(snap["TELEMETRY"]))

        p_snap = snap.get("parent", {})
        for k, v in p_snap.items():
            if k == "_IMPL_players":
                impl = p_ns.get("_IMPL")
                if impl and hasattr(impl, "chassis"):
                    impl.chassis.players = copy.deepcopy(v)
            elif k == "_IMPL_diag":
                impl = p_ns.get("_IMPL")
                if impl and hasattr(impl, "chassis"):
                    impl.chassis.diagnostics = copy.deepcopy(v)
            elif k in p_ns and isinstance(p_ns[k], dict):
                p_ns[k].clear()
                p_ns[k].update(copy.deepcopy(v))


class V3Continuation(ContinuationPolicy):
    """Continuation provider executing frozen V3 policy on simulated rollouts."""

    def __init__(self, agent_fn: Any) -> None:
        self.agent_fn = agent_fn

    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        obs = build_simulated_observation(rollout, player=player)
        try:
            action = self.agent_fn(obs)
        except TypeError:
            try:
                action = self.agent_fn(obs, None)
            except Exception:
                return {"farmer": ["PASS"], "hands": [], "market": []}
        if not isinstance(action, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return action

    def snapshot(self) -> Dict[str, Any]:
        return snapshot_v3_globals(self.agent_fn)

    def restore(self, snap: Dict[str, Any]) -> None:
        restore_v3_globals(self.agent_fn, snap)


class V3BackboneAdapter(BackbonePolicy):
    """Isolates the frozen V3 agent and exposes the formal BackbonePolicy interface."""

    def __init__(
        self,
        tarball_path: Optional[str] = None,
        config: Optional[AECConfig] = None,
        agent_fn: Optional[Callable] = None
    ) -> None:
        self.config = config or AECConfig()
        self._tarball_path = tarball_path or self.config.v3_tarball_path
        self._code_hash = ""
        self._last_called_step = -1
        self._call_count = 0

        if agent_fn is not None:
            self._agent_fn = agent_fn
            self._v3_chassis = getattr(agent_fn, "chassis", None)
            self._code_hash = "EXTERNAL_CALLABLE"
        else:
            self._load_frozen_v3()

    def _load_frozen_v3(self) -> None:
        tar_path = self._tarball_path
        if not os.path.isabs(tar_path):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            tar_path = os.path.join(repo_root, tar_path)

        if not os.path.exists(tar_path):
            raise FileNotFoundError(f"V3 frozen submission tarball missing: {tar_path}")

        with open(tar_path, "rb") as f:
            raw_bytes = f.read()
            self._code_hash = hashlib.sha256(raw_bytes).hexdigest()

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
        impl = ns.get("_PARENT_NS", {}).get("_IMPL", None)
        if impl is not None:
            self._v3_chassis = getattr(impl, "chassis", None)
        else:
            self._v3_chassis = None

    def identity(self) -> str:
        return "V3_STANDALONE"

    def version(self) -> str:
        return "1.0.0-v3-frozen"

    def code_hash(self) -> str:
        return self._code_hash

    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        step = int(observation.get("step", 0) or 0)
        if step == self._last_called_step:
            raise RuntimeError(
                f"CRITICAL AEC INVARIANT BREACH: Baseline agent invoked twice for step {step}!"
            )

        raw_action = self._agent_fn(observation, configuration)
        self._call_count += 1
        self._last_called_step = step
        return copy.deepcopy(raw_action)

    def macro_fingerprint(
        self,
        observation: Dict[str, Any],
        player: int = 0
    ) -> Dict[str, Any]:
        fp = compute_base_macro_fingerprint(observation, player=player)
        fp["backbone_id"] = self.identity()
        return fp

    def snapshot_state(self) -> Dict[str, Any]:
        snap = snapshot_v3_globals(self._agent_fn)
        snap["_last_called_step"] = self._last_called_step
        snap["_call_count"] = self._call_count
        return snap

    def restore_state(self, snapshot: Dict[str, Any]) -> None:
        if not snapshot:
            return
        restore_v3_globals(self._agent_fn, snapshot)
        self._last_called_step = snapshot.get("_last_called_step", -1)
        self._call_count = snapshot.get("_call_count", 0)

    def create_continuation_policy(self) -> ContinuationPolicy:
        return V3Continuation(self._agent_fn)

    def get_future_trajectory(
        self,
        step: int,
        horizon: int,
        player: int = 0,
        n_hands: int = 0
    ) -> List[Dict[str, Any]]:
        if horizon <= 1:
            return []

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
                    act = align_hands(tape[future_step], n_hands)
                    trajectory.append(act)
                else:
                    trajectory.append({
                        "farmer": ["PASS"],
                        "hands": [["PASS"] for _ in range(n_hands)],
                        "market": []
                    })
            return trajectory

        return [{
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(n_hands)],
            "market": []
        } for _ in range(horizon - 1)]

    def reset(self) -> None:
        self._last_called_step = -1
        self._call_count = 0
