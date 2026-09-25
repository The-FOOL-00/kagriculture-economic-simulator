# SPDX-License-Identifier: MIT
"""HMEH Deterministic Chore Executor Layer.

Translates StrategicIntent + EconomicState into multi-unit physical actions
using a 4-Pass Spatial Chore Dispatcher.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from config import CROPS_INFO, MOVES
    from economic_state import EconomicState
    from strategies import StrategicIntent
except ImportError:
    from candidates.v32_hmeh.config import CROPS_INFO, MOVES
    from candidates.v32_hmeh.economic_state import EconomicState
    from candidates.v32_hmeh.strategies import StrategicIntent


def _manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _get_shed_tiles(tiles: List[List[Any]]) -> List[Tuple[int, int]]:
    board = len(tiles)
    half = board // 2
    candidates = [
        (half - 1, half - 1), (half, half - 1),
        (half - 1, half), (half, half)
    ]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]


def _get_next_step(start: Tuple[int, int], target: Tuple[int, int], tiles: List[List[Any]]) -> str:
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target
    moves = []
    
    # Preferred cardinal directions towards target
    if tx > sx and sx + 1 < len(tiles[0]) and tiles[sy][sx + 1] != "LOCKED":
        moves.append("EAST")
    if tx < sx and sx - 1 >= 0 and tiles[sy][sx - 1] != "LOCKED":
        moves.append("WEST")
    if ty > sy and sy + 1 < len(tiles) and tiles[sy + 1][sx] != "LOCKED":
        moves.append("SOUTH")
    if ty < sy and sy - 1 >= 0 and tiles[sy - 1][sx] != "LOCKED":
        moves.append("NORTH")
        
    if not moves:
        # Fallback: any valid non-locked move
        for m, (dx, dy) in [("EAST", (1, 0)), ("WEST", (-1, 0)), ("SOUTH", (0, 1)), ("NORTH", (0, -1))]:
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles) and tiles[ny][nx] != "LOCKED":
                moves.append(m)
                
    return moves[0] if moves else "PASS"


class ChoreExecutor:
    def __init__(self):
        pass
        
    def execute(
        self,
        observation: Dict[str, Any],
        state: EconomicState,
        intent: StrategicIntent
    ) -> Dict[str, Any]:
        """Dispatches chores across farmer and hired hands."""
        player = observation.get("player", 0)
        farms = observation.get("farms", [])
        farm = farms[player] if farms and player < len(farms) else {}
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        hands = [tuple(h) for h in farm.get("hands", [])]
        worker_positions = [farmer_pos] + hands
        n_workers = len(worker_positions)
        
        tiles = farm.get("tiles", [[None] * 10 for _ in range(10)])
        shed_tiles = _get_shed_tiles(tiles)
        
        # Build chore list
        chores: List[Dict[str, Any]] = []
        empty_pastures = list(state.empty_pastures)
        pastures_to_build = max(
            0,
            (intent.cow_target + intent.sheep_target) -
            (state.cow_count + state.sheep_count + len(empty_pastures))
        )
        
        # Weeds
        for pos in state.weed_tiles:
            chores.append({"type": "DIG", "pos": pos, "weight": 95})
            
        # Animals
        for pos in state.unfed_animal_tiles:
            chores.append({"type": "FEED", "pos": pos, "weight": 92})
        for pos in state.uncared_animal_tiles:
            chores.append({"type": "CARE", "pos": pos, "weight": 76})
            
        # Crops
        for s in state.crop_stages:
            pos = s["pos"]
            crop = s["crop"]
            age = s["age"]
            yield_u = s["yield_units"]
            cd = CROPS_INFO.get(crop, {})
            
            # Water
            if not s["watered_today"]:
                chores.append({"type": "WATER", "pos": pos, "weight": 82})
                
            # Harvest (Strict maturity check)
            if crop == "MELON":
                if age >= 10 or yield_u >= 6 or (state.day >= 28 and yield_u >= 1):
                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
            elif crop == "CARROT":
                if age >= 3 or yield_u >= 3 or (state.day >= 28 and yield_u >= 1):
                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
            elif crop == "WHEAT":
                if age >= 4 or yield_u >= 4 or (state.day >= 28 and yield_u >= 1):
                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
            elif crop == "STRAWBERRY":
                if age >= 10 and yield_u > 0:
                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
            elif age >= cd.get("max_yield_day", 4) and yield_u > 0:
                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                
        # Planting on vacant tiles if seeds available
        avail_seeds = dict(state.seed_inventory)
        if sum(avail_seeds.values()) > 0 and state.day <= 26:
            for pos in state.vacant_arable_tiles:
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        # Worker action assignments
        actions: List[List[Any]] = [["PASS"] for _ in range(n_workers)]
        unassigned: List[int] = list(range(n_workers))
        assigned_positions: Set[Tuple[int, int]] = set()
        
        # ---------------------------------------------------------------------
        # PASS 1: STAND-ON INSTANT CHORES (0 movement cost)
        # ---------------------------------------------------------------------
        for w in list(unassigned):
            pos = worker_positions[w]
            x, y = pos
            t = tiles[y][x]
            inv = state.carried_inventory[w] if w < len(state.carried_inventory) else {}
            
            if isinstance(t, dict):
                kind = t.get("kind")
                if kind == "WEED":
                    actions[w] = ["DIG"]
                    unassigned.remove(w); assigned_positions.add(pos); continue
                elif "animal" in t and t.get("animal"):
                    if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                        actions[w] = ["FEED"]
                        inv["WHEAT"] -= 1
                        unassigned.remove(w); assigned_positions.add(pos); continue
                    if t.get("yield_units", 0) > 0:
                        actions[w] = ["HARVEST"]
                        unassigned.remove(w); assigned_positions.add(pos); continue
                    if t.get("fertilizer_available", False):
                        actions[w] = ["COLLECT_FERTILIZER"]
                        unassigned.remove(w); assigned_positions.add(pos); continue
                    if not t.get("cared_today", False):
                        actions[w] = ["CARE"]
                        unassigned.remove(w); assigned_positions.add(pos); continue
                elif kind == "PASTURE" and "animal" not in t:
                    if inv.get("COW", 0) > 0:
                        actions[w] = ["PLACE", "COW"]
                        inv["COW"] -= 1
                        unassigned.remove(w); assigned_positions.add(pos); continue
                    elif inv.get("SHEEP", 0) > 0:
                        actions[w] = ["PLACE", "SHEEP"]
                        inv["SHEEP"] -= 1
                        unassigned.remove(w); assigned_positions.add(pos); continue
                elif kind == "PLANT":
                    is_mature = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                    if is_mature:
                        actions[w] = ["HARVEST"]
                        unassigned.remove(w); assigned_positions.add(pos); continue
                    if not t.get("watered_today", False):
                        actions[w] = ["WATER"]
                        unassigned.remove(w); assigned_positions.add(pos); continue
            elif t is None:
                if pastures_to_build > 0:
                    actions[w] = ["BUILD_PASTURE"]
                    pastures_to_build -= 1
                    empty_pastures.append(pos)
                    unassigned.remove(w); assigned_positions.add(pos); continue
                elif state.day <= 26:
                    for sc in ["MELON", "CARROT", "WHEAT", "STRAWBERRY"]:
                        if avail_seeds.get(sc, 0) > 0:
                            actions[w] = ["PLANT", sc]
                            avail_seeds[sc] -= 1
                            unassigned.remove(w); assigned_positions.add(pos); break

        # ---------------------------------------------------------------------
        # PASS 2: CENTRAL SHED LOGISTICS (Standing on shed)
        # ---------------------------------------------------------------------
        shed = dict(state.shed_inventory)
        for w in list(unassigned):
            pos = worker_positions[w]
            inv = state.carried_inventory[w] if w < len(state.carried_inventory) else {}
            
            if pos in shed_tiles:
                # 1. Animal pickup to stock pastures
                if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                    actions[w] = ["PICKUP", "COW", 1]
                    shed["COW"] -= 1
                    unassigned.remove(w); continue
                elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                    actions[w] = ["PICKUP", "SHEEP", 1]
                    shed["SHEEP"] -= 1
                    unassigned.remove(w); continue
                # 2. Wheat pickup to feed unfed animals
                elif state.unfed_animal_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    take_qty = min(4, shed["WHEAT"])
                    actions[w] = ["PICKUP", "WHEAT", take_qty]
                    shed["WHEAT"] -= take_qty
                    unassigned.remove(w); continue

        # ---------------------------------------------------------------------
        # PASS 3: TARGETED SPATIAL ROUTING
        # ---------------------------------------------------------------------
        rem_chores = [c for c in chores if c["pos"] not in assigned_positions]
        claimed_unfed = set()
        
        for w in list(unassigned):
            pos = worker_positions[w]
            inv = state.carried_inventory[w] if w < len(state.carried_inventory) else {}
            
            # Animal delivery to empty pasture
            if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                if empty_pastures:
                    target = min(empty_pastures, key=lambda p: _manhattan(pos, p))
                    actions[w] = [_get_next_step(pos, target, tiles)]
                    unassigned.remove(w); continue
                    
            # Worker carrying wheat routes to unfed animal
            if inv.get("WHEAT", 0) > 0 and state.unfed_animal_tiles:
                avail_unfed = [p for p in state.unfed_animal_tiles if p not in claimed_unfed]
                target = min(avail_unfed or state.unfed_animal_tiles, key=lambda p: _manhattan(pos, p))
                claimed_unfed.add(target)
                actions[w] = [_get_next_step(pos, target, tiles)]
                unassigned.remove(w); continue
                
            # Worker without wheat heads to shed if animals are hungry
            if inv.get("WHEAT", 0) == 0 and state.unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                if len(claimed_unfed) < len(state.unfed_animal_tiles) and shed_tiles:
                    actions[w] = [_get_next_step(pos, shed_tiles[0], tiles)]
                    unassigned.remove(w); continue

        # ---------------------------------------------------------------------
        # PASS 4: GENERAL CHORES & FALLBACK ROUTING
        # ---------------------------------------------------------------------
        for w in unassigned:
            pos = worker_positions[w]
            if rem_chores:
                best_c = None
                best_score = -999999.0
                for c in rem_chores:
                    dist = _manhattan(pos, c["pos"])
                    score = c["weight"] - dist * 2.0
                    if score > best_score:
                        best_score = score
                        best_c = c
                if best_c:
                    actions[w] = [_get_next_step(pos, best_c["pos"], tiles)]
                    assigned_positions.add(best_c["pos"])
                    rem_chores.remove(best_c)
                    continue
                    
            # Return towards shed if idle
            if pos not in shed_tiles and shed_tiles:
                actions[w] = [_get_next_step(pos, shed_tiles[0], tiles)]
            else:
                actions[w] = ["PASS"]

        return {
            "farmer": actions[0] if actions else ["PASS"],
            "hands": actions[1:] if len(actions) > 1 else [],
            "market": intent.market_orders
        }
