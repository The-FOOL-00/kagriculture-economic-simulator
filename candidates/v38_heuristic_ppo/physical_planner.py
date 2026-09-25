# SPDX-License-Identifier: MIT
"""Kagriculture V38 Physical Planner & Invariance Monitor.

Maintains spatial choreography safety, hand alignment, shed adjacency verification,
and monitors physical trajectory divergence D_phys(t) against the reference heuristic.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple

BOARD_SIZE = 10
SHED_TILES = {(4, 4), (4, 5), (5, 4), (5, 5)}
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def is_shed_adjacent(pos: Tuple[int, int]) -> bool:
    """Checks if a position is adjacent to or on the center shed."""
    x, y = pos
    return x in (3, 4, 5, 6) and y in (3, 4, 5, 6)


def compute_physical_divergence(
    pos_cand: List[Tuple[int, int]],
    pos_ref: List[Tuple[int, int]]
) -> float:
    """Computes Manhattan displacement divergence D_phys between candidate and reference positions."""
    if not pos_cand or not pos_ref:
        return 0.0
    common = min(len(pos_cand), len(pos_ref))
    div = 0.0
    for i in range(common):
        div += abs(pos_cand[i][0] - pos_ref[i][0]) + abs(pos_cand[i][1] - pos_ref[i][1])
    # Add penalty for mismatched unit counts
    div += abs(len(pos_cand) - len(pos_ref)) * 10.0
    return float(div)


class PhysicalPlanner:
    """Enforces deterministic physical dispatch and validates unit chore legality."""
    
    def __init__(self):
        self.last_positions: List[Tuple[int, int]] = []
        
    def align_hands(self, action: Dict[str, Any], real_hand_count: int) -> Dict[str, Any]:
        """Pads or truncates hands list to match real unit count."""
        act = copy.deepcopy(action)
        hands = list(act.get("hands") or [])
        if len(hands) < real_hand_count:
            hands.extend([["PASS"] for _ in range(real_hand_count - len(hands))])
        elif len(hands) > real_hand_count:
            hands = hands[:real_hand_count]
        act["hands"] = hands
        return act

    def sanitize_physical_actions(
        self,
        action: Dict[str, Any],
        positions: List[Tuple[int, int]],
        board_size: int = 10
    ) -> Dict[str, Any]:
        """Ensures unit actions do not move out of bounds or perform illegal shed ops."""
        act = copy.deepcopy(action)
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        
        sanitized = []
        for i, u in enumerate(units):
            if not u:
                sanitized.append(["PASS"])
                continue
            op = u[0]
            pos = positions[i] if i < len(positions) else (0, 0)
            
            # Check move bounds
            if op in MOVES:
                dx, dy = MOVES[op]
                nx, ny = pos[0] + dx, pos[1] + dy
                if not (0 <= nx < board_size and 0 <= ny < board_size):
                    sanitized.append(["PASS"])
                    continue
                    
            # Check shed ops
            if op in ("DROP", "PICKUP") and not is_shed_adjacent(pos):
                sanitized.append(["PASS"])
                continue
                
            sanitized.append(u)
            
        act["farmer"] = sanitized[0] if sanitized else ["PASS"]
        act["hands"] = sanitized[1:] if len(sanitized) > 1 else []
        return act
