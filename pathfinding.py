"""
Fast pathfinding, grid navigation, and movement utilities for Kaggriculture.
"""

from collections import deque
from config import FARMER_MOVES

OPPOSITE_MOVES = {
    (0, -1): "NORTH",
    (0, 1):  "SOUTH",
    (1, 0):  "EAST",
    (-1, 0): "WEST",
}

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_unlocked_shed_tiles(tiles, board_size=10):
    """Return shed access tiles that are currently unlocked."""
    valid = []
    for x, y in SHED_TILES:
        if 0 <= x < board_size and 0 <= y < board_size:
            if tiles[y][x] != "LOCKED":
                valid.append((x, y))
    return valid if valid else [(4, 4)]


def bfs_distance_map(start, tiles, board_size=10):
    """
    Compute shortest distances and predecessors from start to all reachable tiles.
    """
    sx, sy = start
    dist = {start: 0}
    parent = {start: None}
    queue = deque([start])

    while queue:
        cx, cy = queue.popleft()
        for d_name, (dx, dy) in FARMER_MOVES.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                if (nx, ny) not in dist and tiles[ny][nx] != "LOCKED":
                    dist[(nx, ny)] = dist[(cx, cy)] + 1
                    parent[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny))
    return dist, parent


def get_next_step(start, target, tiles, board_size=10):
    """
    Find the single next directional move ("NORTH", "SOUTH", "EAST", "WEST", or "PASS")
    to reach target from start via unlocked tiles.
    """
    if start == target:
        return "PASS"

    sx, sy = start
    tx, ty = target

    # Quick direct check if neighbor
    dx = tx - sx
    dy = ty - sy
    if abs(dx) + abs(dy) == 1:
        move = OPPOSITE_MOVES.get((dx, dy))
        if move and 0 <= tx < board_size and 0 <= ty < board_size and tiles[ty][tx] != "LOCKED":
            return move

    # BFS from target back to start
    dist, parent = bfs_distance_map(target, tiles, board_size)
    if start not in dist:
        # Fallback greedy manhattan step if no path
        for move, (mdx, mdy) in FARMER_MOVES.items():
            nx, ny = sx + mdx, sy + mdy
            if 0 <= nx < board_size and 0 <= ny < board_size and tiles[ny][nx] != "LOCKED":
                if manhattan((nx, ny), target) < manhattan(start, target):
                    return move
        return "PASS"

    # Follow parent from start towards target
    # Since dist is from target, find neighbor of start with minimal distance to target
    best_move = "PASS"
    min_d = 999999
    for move, (mdx, mdy) in FARMER_MOVES.items():
        nx, ny = sx + mdx, sy + mdy
        pos = (nx, ny)
        if pos in dist and dist[pos] < min_d:
            min_d = dist[pos]
            best_move = move

    return best_move
