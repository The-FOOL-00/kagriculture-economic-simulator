# SPDX-License-Identifier: MIT
"""V25 P3 Unified Macro Planner Backbone Adapter conforming to BackbonePolicy (§6)."""

from __future__ import annotations

import copy
import hashlib
import os
import tarfile
from typing import Any, Callable, Dict, List, Optional

from aec.backbone.interface import BackbonePolicy, ContinuationPolicy
from aec.backbone.utils import (
    align_hands,
    build_simulated_observation,
    compute_base_macro_fingerprint,
    _get,
    _int
)
from aec.backbone.v3_adapter import restore_v3_globals, snapshot_v3_globals
from aec.config import AECConfig


def _tile_at(tiles: Any, pos: Any) -> Any:
    try:
        x, y = int(pos[0]), int(pos[1])
        return tiles[y][x]
    except (TypeError, ValueError, IndexError):
        return "LOCKED"


def apply_p3_labor_dispatch(action: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """Applies in-place zero-inventory labor dispatch to PASS units on weeds or dry crops."""
    try:
        p = _int(_get(observation, "player", 0))
        farms = _get(observation, "farms", [])
        if p >= len(farms):
            return action
        farm = farms[p]
        tiles = _get(farm, "tiles", [])
        farmer_pos = _get(farm, "farmer")
        hands = _get(farm, "hands", []) or []
        positions = [farmer_pos] + list(hands)

        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        modified = False

        for i in range(min(len(units), len(positions))):
            act = units[i]
            pos = positions[i]
            if not act or act[0] != "PASS" or pos is None:
                continue

            x, y = int(pos[0]), int(pos[1])
            tile = _tile_at(tiles, (x, y))
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")

            # Chore 1: Water dry growing crop
            if kind == "PLANT" and not tile.get("watered_today", False):
                units[i] = ["WATER"]
                modified = True
                continue

            # Chore 2: Dig blocking weed
            if kind == "WEED":
                units[i] = ["DIG"]
                modified = True
                continue

        if modified:
            action = dict(action)
            action["farmer"] = units[0]
            action["hands"] = units[1:]

    except Exception:
        pass

    return action


class V25P3Continuation(ContinuationPolicy):
    """Continuation provider executing V25 P3 unified policy on simulated rollouts."""

    def __init__(self, v3_agent_callable: Any) -> None:
        self.v3_agent_callable = v3_agent_callable

    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        step = rollout.step
        # Stage 1: Macro Capital Allocation (Opening Turn)
        if step == 0:
            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
            }

        # Stage 2: Underlying Route Compilation Baseline
        obs = build_simulated_observation(rollout, player=player)
        try:
            action = self.v3_agent_callable(obs)
        except TypeError:
            try:
                action = self.v3_agent_callable(obs, None)
            except Exception:
                action = {"farmer": ["PASS"], "hands": [], "market": []}
        if not isinstance(action, dict):
            action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Stage 3: Coherent Labor Optimization (In-Place / Zero Inventory)
        return apply_p3_labor_dispatch(action, obs)

    def snapshot(self) -> Dict[str, Any]:
        return snapshot_v3_globals(self.v3_agent_callable)

    def restore(self, snap: Dict[str, Any]) -> None:
        restore_v3_globals(self.v3_agent_callable, snap)


class V25P3BackboneAdapter(BackbonePolicy):
    """Backbone adapter for V25 P3 Unified Macro Planner conforming to BackbonePolicy."""

    def __init__(
        self,
        tarball_path: Optional[str] = None,
        candidate_path: Optional[str] = None,
        config: Optional[AECConfig] = None
    ) -> None:
        self.config = config or AECConfig()
        self._tarball_path = tarball_path or self.config.v3_tarball_path
        self._candidate_path = candidate_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "candidates", "v25_p3_unified.py"
        )
        self._code_hash = ""
        self._last_called_step = -1
        self._call_count = 0

        self._load_v25_p3()

    def _load_v25_p3(self) -> None:
        # 1. Compute hash of candidates/v25_p3_unified.py
        cand_path = os.path.abspath(self._candidate_path)
        if os.path.exists(cand_path):
            with open(cand_path, "rb") as f:
                self._code_hash = hashlib.sha256(f.read()).hexdigest()
        else:
            self._code_hash = "V25_P3_INLINE"

        # 2. Extract and load an isolated V3 instance
        tar_path = self._tarball_path
        if not os.path.isabs(tar_path):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            tar_path = os.path.join(repo_root, tar_path)

        if not os.path.exists(tar_path):
            raise FileNotFoundError(f"V3 frozen submission tarball missing: {tar_path}")

        with tarfile.open(tar_path, "r:gz") as tar:
            main_member = tar.extractfile("main.py")
            if main_member is None:
                raise RuntimeError("Failed to extract main.py from V3 tarball")
            v3_code = main_member.read().decode("utf-8")

        ns: Dict[str, Any] = {"__name__": f"v25_p3_isolated_v3_{id(self)}"}
        exec(compile(v3_code, "frozen_v3_for_p3.py", "exec"), ns)
        agent_callable = ns.get("agent")
        if not callable(agent_callable):
            raise RuntimeError("V3 frozen main.py does not define callable 'agent'")

        self._v3_agent_callable = agent_callable
        impl = ns.get("_PARENT_NS", {}).get("_IMPL", None)
        self._v3_chassis = getattr(impl, "chassis", None) if impl is not None else None

    def identity(self) -> str:
        return "V25_P3_UNIFIED"

    def version(self) -> str:
        return "1.0.0-v25-p3"

    def code_hash(self) -> str:
        return self._code_hash

    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        step = _int(_get(observation, "step", 0))
        if step == self._last_called_step:
            raise RuntimeError(
                f"CRITICAL AEC INVARIANT BREACH: Baseline agent invoked twice for step {step}!"
            )

        # Stage 1: Macro Capital Allocation (Opening Turn)
        if step == 0:
            action = {
                "farmer": ["PASS"],
                "hands": [],
                "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
            }
            self._call_count += 1
            self._last_called_step = step
            return copy.deepcopy(action)

        # Stage 2: Low-Level Route Compilation & Reactive Baseline
        raw_action = self._v3_agent_callable(observation, configuration)
        if not isinstance(raw_action, dict):
            raw_action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Stage 3: Coherent Labor Optimization (In-Place / Zero Inventory)
        final_action = apply_p3_labor_dispatch(raw_action, observation)

        self._call_count += 1
        self._last_called_step = step
        return copy.deepcopy(final_action)

    def macro_fingerprint(
        self,
        observation: Dict[str, Any],
        player: int = 0
    ) -> Dict[str, Any]:
        fp = compute_base_macro_fingerprint(observation, player=player)
        fp["backbone_id"] = self.identity()
        fp["open_units"] = 30
        return fp

    def snapshot_state(self) -> Dict[str, Any]:
        snap = snapshot_v3_globals(self._v3_agent_callable)
        snap["_last_called_step"] = self._last_called_step
        snap["_call_count"] = self._call_count
        return snap

    def restore_state(self, snapshot: Dict[str, Any]) -> None:
        if not snapshot:
            return
        restore_v3_globals(self._v3_agent_callable, snapshot)
        self._last_called_step = snapshot.get("_last_called_step", -1)
        self._call_count = snapshot.get("_call_count", 0)

    def create_continuation_policy(self) -> ContinuationPolicy:
        return V25P3Continuation(self._v3_agent_callable)

    def get_future_trajectory(
        self,
        step: int,
        horizon: int,
        player: int = 0,
        n_hands: int = 0
    ) -> List[Dict[str, Any]]:
        if horizon <= 1:
            return []

        chassis = self._v3_chassis or getattr(self._v3_agent_callable, "chassis", None)
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
