"""Isolated, Deterministic Blocked-Action / Weed Repair Engine for V51.

Reconstructs and verifies Kaito Fukami's weed repair mechanism in isolation.
Supports:
- Farmer and all farm hands independently (strict per-actor state tracking).
- Simultaneous multi-actor collisions.
- Multiple consecutive collisions.
- Replay buffer with 1-turn offset tracking.
- Zero-drift guarantee when no blockers are present.
- Support for PLANT and BUILD_PASTURE operations on WEED tiles.
- Telemetry and exact state transition recording.
"""

from __future__ import annotations
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple


def get_tile(farm: Dict[str, Any], position: Optional[List[int]]) -> Any:
    """Retrieve tile object safely from farm grid."""
    if not position or len(position) < 2:
        return "LOCKED"
    try:
        x, y = int(position[0]), int(position[1])
        tiles = farm.get("tiles", []) or []
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
            return tiles[y][x]
        return "LOCKED"
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def get_actor_trace_action(action_tape: List[Dict[str, Any]], step: int, actor: Any) -> List[str]:
    """Retrieve the scheduled action for an actor from an action tape at step."""
    if not action_tape:
        return ["PASS"]
    idx = min(max(int(step), 0), len(action_tape) - 1)
    entry = action_tape[idx] or {}
    if actor == "farmer" or actor == 0:
        return copy.deepcopy(entry.get("farmer", ["PASS"]) or ["PASS"])
    hands = entry.get("hands", []) or []
    h_idx = int(actor) - 1 if isinstance(actor, int) and actor > 0 else (int(actor) if isinstance(actor, int) else 0)
    if 0 <= h_idx < len(hands):
        return copy.deepcopy(hands[h_idx] or ["PASS"])
    return ["PASS"]


class WeedRepairEngine:
    """Stateful, local weed repair transaction controller."""

    def __init__(self, replay_steps: int = 8, stop_on_match: bool = True):
        self.replay_steps = max(0, int(replay_steps))
        self.stop_on_match = bool(stop_on_match)
        self.states: Dict[int, Dict[str, Any]] = {0: {"last_step": -1, "active": {}}, 1: {"last_step": -1, "active": {}}}
        self.telemetry: Dict[str, Any] = {
            "total_calls": 0,
            "collisions": 0,
            "dig_actions": 0,
            "retry_actions": 0,
            "replay_actions": 0,
            "early_matches": 0,
            "expired_transactions": 0,
            "by_operation": {"PLANT": 0, "BUILD_PASTURE": 0},
            "history": [],
        }

    def reset(self):
        """Reset state across episodes."""
        self.states = {0: {"last_step": -1, "active": {}}, 1: {"last_step": -1, "active": {}}}

    def process_turn(
        self,
        obs: Dict[str, Any],
        raw_action: Dict[str, Any],
        action_tape_lookup: Optional[Callable[[int, Any], List[str]]] = None,
    ) -> Dict[str, Any]:
        """Intercepts raw_action and applies weed repair if collisions are detected."""
        self.telemetry["total_calls"] += 1
        step = max(0, int(obs.get("step", 0) or 0))
        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        game = self.states[seat]

        # Episode boundary or rewound step
        if step == 0 or "active" not in game or step < game.get("last_step", -1):
            game = {"last_step": step, "active": {}}
            self.states[seat] = game

        game["last_step"] = step
        active = game["active"]

        farms = list(obs.get("farms", []) or [])
        farm = farms[seat] if seat < len(farms) else {}
        positions = [farm.get("farmer"), *(farm.get("hands", []) or [])]

        farmer_act = raw_action.get("farmer", ["PASS"]) or ["PASS"]
        hands_act = list(raw_action.get("hands", []) or [])
        unit_actions = [farmer_act] + hands_act

        # ---------------------------------------------------------------------
        # Phase 1: Service existing transactions in flight
        # ---------------------------------------------------------------------
        for actor, transaction in list(active.items()):
            index = 0 if actor == "farmer" else int(actor) + 1
            if index >= len(unit_actions):
                active.pop(actor, None)
                self.telemetry["expired_transactions"] += 1
                continue

            age = step - transaction["start"]

            # Turn t + 1: Retry intended action
            if age == 1:
                unit_actions[index] = copy.deepcopy(transaction["intended"])
                self.telemetry["retry_actions"] += 1
                self.telemetry["history"].append({
                    "step": step, "seat": seat, "actor": actor,
                    "event": "RETRY", "action": unit_actions[index]
                })
                continue

            # Turn t + 2 .. t + 1 + replay_steps: Replay previous scheduled action (offset -1)
            if 2 <= age <= 1 + self.replay_steps:
                if action_tape_lookup:
                    previous = action_tape_lookup(step - 1, actor)
                else:
                    previous = unit_actions[index]

                if self.stop_on_match and unit_actions[index] == previous:
                    active.pop(actor, None)
                    self.telemetry["early_matches"] += 1
                    self.telemetry["history"].append({
                        "step": step, "seat": seat, "actor": actor,
                        "event": "EARLY_MATCH", "action": unit_actions[index]
                    })
                    continue

                unit_actions[index] = previous
                self.telemetry["replay_actions"] += 1
                self.telemetry["history"].append({
                    "step": step, "seat": seat, "actor": actor,
                    "event": "REPLAY_OFFSET", "action": unit_actions[index]
                })
                continue

            # Expiration
            active.pop(actor, None)
            self.telemetry["expired_transactions"] += 1
            self.telemetry["history"].append({
                "step": step, "seat": seat, "actor": actor,
                "event": "EXPIRED"
            })

        # ---------------------------------------------------------------------
        # Phase 2: Detect new collisions
        # ---------------------------------------------------------------------
        for index, (pos, intended) in enumerate(zip(positions, unit_actions)):
            actor = "farmer" if index == 0 else index - 1
            if actor in active:
                continue
            if not isinstance(intended, list) or not intended:
                continue

            op = intended[0]
            if op not in ("BUILD_PASTURE", "PLANT"):
                continue

            tile = get_tile(farm, pos)
            is_weed = False
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                is_weed = True
            elif isinstance(tile, str) and tile == "WEED":
                is_weed = True

            if not is_weed:
                continue

            # Collision confirmed -> open transaction & issue DIG
            active[actor] = {
                "start": step,
                "intended": copy.deepcopy(intended),
            }
            unit_actions[index] = ["DIG"]
            self.telemetry["collisions"] += 1
            self.telemetry["dig_actions"] += 1
            self.telemetry["by_operation"][op] = self.telemetry["by_operation"].get(op, 0) + 1
            self.telemetry["history"].append({
                "step": step, "seat": seat, "actor": actor,
                "event": "COLLISION_DIG", "intended": intended, "pos": pos
            })

        out_action = copy.deepcopy(raw_action)
        out_action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
        out_action["hands"] = unit_actions[1:]
        return out_action
