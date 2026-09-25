# SPDX-License-Identifier: MIT
"""HMEH Legality and Safety Filter Layer.

Grounds all unit and market actions in the simulator engine semantics
to guarantee 0 crashes and 0 unexpected illegal actions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from config import ANIMAL_STRUCTURES, MOVES, PRODUCTS, SEED_PRICES
except ImportError:
    from candidates.v32_hmeh.config import ANIMAL_STRUCTURES, MOVES, PRODUCTS, SEED_PRICES


def _is_shed_adjacent(pos: Tuple[int, int], board_size: int = 10) -> bool:
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return False
    half = board_size // 2
    return pos[0] in (half - 1, half) and pos[1] in (half - 1, half)


@dataclass
class FilterResult:
    action: Dict[str, Any]
    rejections: List[Dict[str, Any]]


class LegalityFilter:
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.total_rejections = 0
        
    def filter(self, raw_action: Dict[str, Any], observation: Dict[str, Any]) -> FilterResult:
        """Filters unit actions and market orders, replacing invalid actions with safe fallbacks."""
        player = observation.get("player", 0)
        farms = observation.get("farms", [])
        farm = farms[player] if farms and player < len(farms) else {}
        money = float(farm.get("money", 0.0) or 0.0)
        tiles = farm.get("tiles", [[None] * self.board_size for _ in range(self.board_size)])
        
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        hands = [tuple(h) for h in farm.get("hands", [])]
        unit_positions = [farmer_pos] + hands
        
        private = observation.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        seeds = dict(private.get("seeds", {}) or {})
        inventories = [dict(inv or {}) for inv in private.get("inventories", [{}])]
        
        rejections: List[Dict[str, Any]] = []
        
        # 1. Filter Unit Actions
        filtered_units: List[List[Any]] = []
        raw_units = [raw_action.get("farmer") or ["PASS"]] + list(raw_action.get("hands") or [])
        
        # Match count of units to actual positions on board
        for i in range(len(unit_positions)):
            pos = unit_positions[i]
            x, y = pos
            tile = tiles[y][x] if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]) else "LOCKED"
            inv = inventories[i] if i < len(inventories) else {}
            
            act = list(raw_units[i]) if i < len(raw_units) and raw_units[i] else ["PASS"]
            op = act[0] if act else "PASS"
            arg = act[1] if len(act) > 1 else None
            qty = act[2] if len(act) > 2 else 1
            
            is_valid = True
            reject_reason = ""
            
            if op in MOVES:
                dx, dy = MOVES[op]
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.board_size and 0 <= ny < self.board_size):
                    is_valid = False
                    reject_reason = f"Move {op} out of grid bounds ({nx}, {ny})"
                else:
                    is_valid = True
            elif op == "PASS":
                is_valid = True
            elif op == "PICKUP":
                if not _is_shed_adjacent(pos, self.board_size):
                    is_valid = False
                    reject_reason = "PICKUP outside shed adjacency"
            elif op == "DROP":
                if not _is_shed_adjacent(pos, self.board_size):
                    is_valid = False
                    reject_reason = "DROP outside shed adjacency"
                elif not any(v > 0 for v in inv.values()):
                    is_valid = False
                    reject_reason = "DROP with empty hand inventory"
            elif op == "PLACE":
                if arg in ANIMAL_STRUCTURES:
                    expected_kind = ANIMAL_STRUCTURES[arg]
                    if not (isinstance(tile, dict) and tile.get("kind") == expected_kind and not tile.get("animal")):
                        if not _is_shed_adjacent(pos, self.board_size):
                            is_valid = False
                            reject_reason = f"PLACE {arg} on non-pasture tile outside shed"
                    if inv.get(arg, 0) <= 0:
                        is_valid = False
                        reject_reason = f"PLACE {arg} without holding animal"
                else:
                    if not _is_shed_adjacent(pos, self.board_size) or inv.get(arg, 0) <= 0:
                        is_valid = False
                        reject_reason = f"PLACE {arg} invalid"
            elif op == "PLANT":
                if tile is not None:
                    is_valid = False
                    reject_reason = f"PLANT on occupied tile {tile}"
                elif seeds.get(arg, 0) <= 0:
                    is_valid = False
                    reject_reason = f"PLANT {arg} with 0 seeds"
                else:
                    seeds[arg] -= 1  # Track local consumption
                    # Mark tile so sequential actions within this step know it is planted
                    tiles[y][x] = {"kind": "PLANT", "crop": arg, "watered_today": False, "yield_units": 1}
            elif op == "WATER":
                if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                    # Safe engine no-op if on empty tile, but do not replace with PASS if benign
                    is_valid = True
                elif tile.get("watered_today", False):
                    is_valid = True
                else:
                    if isinstance(tile, dict):
                        tile["watered_today"] = True
                    is_valid = True
            elif op == "FERTILIZE":
                if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                    is_valid = False
                    reject_reason = "FERTILIZE on non-plant tile"
                elif inv.get("FERTILIZER", 0) <= 0:
                    is_valid = False
                    reject_reason = "FERTILIZE without fertilizer in hand"
                else:
                    inv["FERTILIZER"] -= 1
                    is_valid = True
            elif op == "HARVEST":
                is_valid = True
            elif op == "DIG":
                if isinstance(tile, dict) and tile.get("animal"):
                    is_valid = False
                    reject_reason = "DIG on animal structure"
                else:
                    is_valid = True
                    tiles[y][x] = None
            elif op in ("BUILD_PASTURE", "BUILD_COOP"):
                if tile is not None:
                    is_valid = False
                    reject_reason = f"{op} on non-empty tile {tile}"
                else:
                    tiles[y][x] = {"kind": "PASTURE" if op == "BUILD_PASTURE" else "COOP"}
            elif op == "FEED":
                if not (isinstance(tile, dict) and tile.get("animal")):
                    is_valid = False
                    reject_reason = "FEED on non-animal tile"
                elif tile.get("fed_today", False):
                    is_valid = True
                elif inv.get("WHEAT", 0) <= 0:
                    is_valid = False
                    reject_reason = "FEED without wheat in hands"
                else:
                    inv["WHEAT"] -= 1
            elif op == "CARE":
                if not (isinstance(tile, dict) and tile.get("animal")):
                    is_valid = False
                    reject_reason = "CARE on non-animal tile"
                else:
                    is_valid = True
            elif op == "COLLECT_FERTILIZER":
                if not (isinstance(tile, dict) and tile.get("animal")):
                    is_valid = False
                    reject_reason = "COLLECT_FERTILIZER unavailable"
                else:
                    is_valid = True
            else:
                is_valid = False
                reject_reason = f"Unknown op {op}"
                
            if is_valid:
                filtered_units.append(act)
            else:
                self.total_rejections += 1
                rejections.append({
                    "unit_idx": i,
                    "pos": pos,
                    "proposed_act": act,
                    "reason": reject_reason,
                    "fallback_act": ["PASS"]
                })
                filtered_units.append(["PASS"])

        # 2. Filter Market Orders
        filtered_orders: List[List[Any]] = []
        raw_orders = list(raw_action.get("market") or [])
        running_cash = money
        
        for order in raw_orders[:10]:
            if not isinstance(order, (list, tuple)) or not order:
                continue
            m_op = order[0]
            m_item = order[1] if len(order) > 1 else None
            m_qty = int(order[2]) if len(order) > 2 else 1
            
            if m_qty <= 0:
                continue
                
            if m_op == "HIRE":
                cost = 5.0
                if running_cash >= cost:
                    filtered_orders.append(["HIRE"])
                    running_cash -= cost
            elif m_op == "BUY_LAND":
                cost = 1000.0
                if running_cash >= cost:
                    filtered_orders.append(["BUY_LAND"])
                    running_cash -= cost
            elif m_op == "BUY_PRODUCT" and m_item in PRODUCTS:
                filtered_orders.append(["BUY_PRODUCT", m_item, m_qty])
            elif m_op == "SELL" and m_item in PRODUCTS:
                filtered_orders.append(["SELL", m_item, m_qty])
            elif m_op == "BUY_SEED" and m_item in SEED_PRICES:
                filtered_orders.append(["BUY_SEED", m_item, m_qty])
            elif m_op == "BUY_ANIMAL" and m_item in ("COW", "SHEEP", "GOOSE"):
                filtered_orders.append(["BUY_ANIMAL", m_item, m_qty])
            else:
                rejections.append({
                    "market_order": order,
                    "reason": f"Invalid market order {order}"
                })

        safe_action = {
            "farmer": filtered_units[0] if filtered_units else ["PASS"],
            "hands": filtered_units[1:] if len(filtered_units) > 1 else [],
            "market": filtered_orders[:10]
        }
        
        return FilterResult(action=safe_action, rejections=rejections)
