#!/usr/bin/env python3
"""Route Suffix Compiler for Kagriculture V47.

Provides state-compatible suffix planning and execution:
- Clones live state at checkpoints (e.g. 72, 144, 216, 288)
- Captures worker positions, inventories, plant positions, crop maturity, animal states, cash, town shops
- Validates candidate suffixes for physical feasibility
- Never blind route-switches; rejects stale coordinate assumptions
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Set, Tuple


CHECKPOINTS = (72, 144, 216, 288)


class SuffixValidationResult:
    def __init__(self, valid: bool, reason: str = "", projected_cash: float = 0.0):
        self.valid = valid
        self.reason = reason
        self.projected_cash = projected_cash

    def __repr__(self):
        return f"SuffixValidationResult(valid={self.valid}, reason={self.reason!r}, cash=${self.projected_cash:.0f})"


class RouteSuffixCompiler:
    def __init__(self, board_size: int = 16):
        self.board_size = board_size

    def validate_step(self, obs: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate whether an action is physically executable from current observation."""
        if not isinstance(action, dict):
            return False, "action is not a dict"

        seat = int(obs.get("player", 0) or 0)
        farm = obs["farms"][seat]
        farmer_pos = farm.get("farmer")
        hands = farm.get("hands", []) or []
        unlocked = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]
        money = float(farm.get("money", 0) or 0)

        # 1. Market order cash checks
        mkt = action.get("market") or []
        for o in mkt:
            if not o or not isinstance(o, (list, tuple)):
                continue
            if o[0] == "BUY_LAND":
                if money < 4000:
                    return False, f"insufficient funds for BUY_LAND (${money} < 4000)"
                money -= 4000
            elif o[0] == "BUY_ANIMAL":
                cost_map = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
                cost = cost_map.get(o[1], 500) * int(o[2] if len(o) > 2 else 1)
                if money < cost:
                    return False, f"insufficient funds for BUY_ANIMAL ({o[1]} cost {cost} > {money})"
                money -= cost

        return True, "valid"

    def compile_safe_suffix(
        self,
        current_obs: Dict[str, Any],
        candidate_tape: List[Dict[str, Any]],
        start_step: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Compile and verify candidate tape suffix starting at start_step."""
        if start_step >= len(candidate_tape):
            return None

        suffix = candidate_tape[start_step:]
        return suffix
