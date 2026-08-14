"""
=============================================================================
ENGINE: DEADLINE-AWARE LABOR SCHEDULER & SPATIAL ASSIGNMENT
=============================================================================
Coordinates farmer and farm hands to execute time-critical tasks with zero starvation.
=============================================================================
"""

from config import fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles


class LaborScheduler:
    def __init__(self):
        pass

    def compute_daily_hire_count(self, world_state, pending_chore_count):
        """
        Determines the optimal number of farm hands to hire for the day.
        """
        if world_state.hour != 0:
            return world_state.hires_today

        unlocked_quads = len(world_state.unlocked_quadrants)
        money = world_state.money

        if world_state.day <= 1:
            target_workers = 3
        elif world_state.day <= 4:
            target_workers = 4
        else:
            if unlocked_quads == 1:
                target_workers = min(4, max(2, (pending_chore_count + 8) // 10))
            elif unlocked_quads == 2:
                target_workers = min(5, max(3, (pending_chore_count + 10) // 11))
            else:
                target_workers = min(6, max(4, (pending_chore_count + 12) // 12))

        target_hands = max(0, target_workers - 1)
        
        # Strict liquidity budget check
        if money < 10:
            target_hands = min(1, target_hands)
        elif money < 50:
            target_hands = min(2, target_hands)
        elif money < 250:
            target_hands = min(3, target_hands)

        return target_hands

    def assign_worker_actions(self, world_state, chores):
        """
        Assigns actions to farmer and farm hands, optimizing spatial proximity.
        """
        num_workers = 1 + len(world_state.hands)
        worker_positions = [world_state.farmer_pos] + list(world_state.hands)
        worker_inventories = world_state.inventories
        available_seeds = dict(world_state.seeds)
        unlocked_sheds = get_unlocked_shed_tiles(world_state.tiles)

        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))
        assigned_chore_positions = set()

        # Pass 1: Stand-on chores (Instant execution)
        for w_idx in list(unassigned_workers):
            pos = worker_positions[w_idx]
            x, y = pos
            tile = world_state.tiles[y][x]
            inv = worker_inventories[w_idx] if w_idx < len(worker_inventories) else {}

            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    actions[w_idx] = ["DIG"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                elif kind == "PLANT":
                    # Check harvest
                    pos_chores = [c for c in chores if c["pos"] == pos and c["type"] == "HARVEST"]
                    if pos_chores:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Check water
                    if not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None and world_state.day <= 26:
                # Stand-on plant
                planted = False
                for seed_crop in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                    if available_seeds.get(seed_crop, 0) > 0:
                        actions[w_idx] = ["PLANT", seed_crop]
                        available_seeds[seed_crop] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        planted = True
                        break
                if planted:
                    continue

        # Pass 2: Spatial routing to nearest high-value chore
        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]

        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if not remaining_chores:
                if w_pos not in unlocked_sheds:
                    move = get_next_step(w_pos, unlocked_sheds[0], world_state.tiles)
                    actions[w_idx] = [move]
                else:
                    actions[w_idx] = ["PASS"]
                continue

            best_chore = None
            best_score = -999999.0
            for chore in remaining_chores:
                dist = manhattan(w_pos, chore["pos"])
                score = chore["weight"] - dist * 2.2
                if score > best_score:
                    best_score = score
                    best_chore = chore

            if best_chore:
                target_pos = best_chore["pos"]
                remaining_chores.remove(best_chore)
                assigned_chore_positions.add(target_pos)
                
                move = get_next_step(w_pos, target_pos, world_state.tiles)
                actions[w_idx] = [move]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }
