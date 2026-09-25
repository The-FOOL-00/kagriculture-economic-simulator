# SPDX-License-Identifier: MIT
"""
Path Generator for Terminal Physical Search.
Generates exact legal unit action sequences (movements, harvest, drop) over the remaining horizon.
"""
from typing import List, Tuple, Dict, Any
from candidates.v32_p11_terminal.terminal_state import nearest_shed_tile

def generate_manhattan_moves(start: Tuple[int, int], end: Tuple[int, int]) -> List[List[str]]:
    moves = []
    cx, cy = start
    tx, ty = end
    
    # Horizontal moves
    while cx < tx:
        moves.append(["EAST"])
        cx += 1
    while cx > tx:
        moves.append(["WEST"])
        cx -= 1
        
    # Vertical moves
    while cy < ty:
        moves.append(["SOUTH"])
        cy += 1
    while cy > ty:
        moves.append(["NORTH"])
        cy -= 1
        
    return moves

def build_worker_plan(
    start_pos: Tuple[int, int],
    target_pos: Tuple[int, int],
    target_op: str,
    total_steps: int
) -> List[List[str]]:
    """
    Generates action sequence for a single worker:
    1. Walk to target
    2. Execute target_op (HARVEST or COLLECT_FERTILIZER)
    3. Walk to nearest shed access tile
    4. Execute DROP
    5. Pad remaining steps with PASS
    """
    actions = []
    
    # 1. Walk to target
    actions.extend(generate_manhattan_moves(start_pos, target_pos))
    
    # 2. Perform harvest / collection
    actions.append([target_op])
    
    # 3. Walk to shed
    shed_tile = nearest_shed_tile(target_pos)
    actions.extend(generate_manhattan_moves(target_pos, shed_tile))
    
    # 4. Drop into shed
    actions.append(["DROP"])
    
    # 5. Pad with PASS if remaining
    while len(actions) < total_steps:
        actions.append(["PASS"])
        
    return actions[:total_steps]
