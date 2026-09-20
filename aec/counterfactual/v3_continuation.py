# SPDX-License-Identifier: MIT
"""Frozen V3 Dynamic Continuation Policy and State Isolation (§11, §17, §20).

Provides guaranteed zero-leakage snapshotting and dynamic forward continuation
using the true frozen V3 baseline agent closure on simulated observations.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from aec.config import BOARD_SIZE, TURNS_PER_DAY


def snapshot_v3_state(agent_fn: Any) -> Dict[str, Any]:
    """Capture a complete, isolated memory snapshot of the frozen V3 agent state (§20)."""
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


def restore_v3_state(agent_fn: Any, snap: Dict[str, Any]) -> None:
    """Restore the frozen V3 agent state exactly to a previous snapshot (§20)."""
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


def build_simulated_observation(
    rollout: Any,
    player: int = 0,
    opponent_econ: Optional[Any] = None,
) -> Dict[str, Any]:
    """Construct a full Kaggle-compliant observation dict from a ShadowRolloutState (§11)."""
    cur_step = rollout.step
    day = cur_step // TURNS_PER_DAY
    hour = cur_step % TURNS_PER_DAY

    # Derive farm quadrants
    unlocked_quads = ["NW"]
    # If board has unlocked tiles in NE/SW/SE:
    if hasattr(rollout, "tiles") and len(rollout.tiles) == 10:
        if rollout.tiles[0][9] != "LOCKED":
            unlocked_quads.append("NE")
        if rollout.tiles[9][0] != "LOCKED":
            unlocked_quads.append("SW")
        if rollout.tiles[9][9] != "LOCKED":
            unlocked_quads.append("SE")

    own_farm = {
        "money": rollout.money,
        "farmer": list(rollout.farmer_pos),
        "hands": [list(p) for p in rollout.hands_pos],
        "tiles": copy.deepcopy(rollout.tiles),
        "hires_today": rollout.hires_today,
        "unlocked_quadrants": list(unlocked_quads),
    }

    opp_cash = getattr(rollout, "opp_money", 3000.0)
    opp_farm = {
        "money": opp_cash,
        "farmer": [4, 4],
        "hands": [],
        "tiles": copy.deepcopy(rollout.tiles),
        "hires_today": 0,
        "unlocked_quadrants": ["NW"],
    }

    farms = [own_farm, opp_farm] if player == 0 else [opp_farm, own_farm]

    if hasattr(rollout, "get_private_dict") and callable(rollout.get_private_dict):
        private_dict = rollout.get_private_dict()
    else:
        private_dict = {
            "shed": getattr(rollout, "shed", {}),
            "seeds": getattr(rollout, "seeds", {}),
            "inventories": [{}, {}],
        }

    return {
        "remainingOverageTime": 60,
        "step": cur_step,
        "player": player,
        "farms": farms,
        "market": {
            "inventory": copy.deepcopy(rollout.market_inv),
            "prices": copy.deepcopy(rollout.market_prices),
        },
        "town": {
            "unlocked_shops": list(rollout.unlocked_shops),
        },
        "day": day,
        "hour": hour,
        "private": {
            "shed": copy.deepcopy(private_dict["shed"]),
            "seeds": copy.deepcopy(private_dict["seeds"]),
            "inventories": copy.deepcopy(private_dict["inventories"]),
        },
    }


class V3ContinuationPolicy:
    """Executes endogenous frozen V3 policy during shadow counterfactual rollouts (§11)."""

    def __init__(self, v3_agent_callable: Any) -> None:
        self.agent_fn = v3_agent_callable

    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        """Query the frozen V3 agent for its continuation action given the simulated rollout state."""
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
