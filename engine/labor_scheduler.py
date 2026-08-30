"""
=============================================================================
ENGINE: HIGH-PERFORMANCE UNIFIED LABOR SCHEDULER (CORRECTED)
=============================================================================
Coordinates the Farmer and hired Farm Hands with deadline-aware prioritization:
1. Animal Care & Feeding (Prevent starvation & maximize care bonuses)
2. Immediate Harvests (Crops & Livestock products)
3. Weed Digging & Daily Watering (Prevent plant decay)
4. Pasture & Coop Construction + Animal Logistics (Pickup from Shed & Placement)
5. Crop Planting & Fertilizer Spreading
6. Optimal Spatial Assignment using Priority-Distance Bipartite Scoring
=============================================================================
"""

from config import fib_hire_cost
from pathfinding import manhattan, get_next_step, get_unlocked_shed_tiles


class LaborScheduler:
    def __init__(self):
        pass

    def compute_daily_hire_count(self, world_state, pending_chore_count):
        """
        Calculates optimal farm hands to hire for the day at hour 0.
        """
        if world_state.hour != 0:
            return world_state.hires_today

        unlocked_quads = len(world_state.unlocked_quadrants)
        if unlocked_quads == 1:
            target_hands = min(3, max(2, (pending_chore_count + 6) // 8))
        elif unlocked_quads == 2:
            target_hands = min(5, max(3, (pending_chore_count + 8) // 9))
        else:
            target_hands = min(6, max(4, (pending_chore_count + 10) // 10))

        return target_hands

    def assign_worker_actions(self, world_state, chores, structures_to_build=None, unfed_animal_tiles=None, care_animals=True, use_fert_on_crops=False):
        """
        Unified spatial worker assignment for all crop and livestock tasks.
        """
        num_workers = 1 + len(world_state.hands)
        worker_positions = [world_state.farmer_pos] + list(world_state.hands)
        worker_inventories = [dict(inv) for inv in world_state.inventories]
        while len(worker_inventories) < num_workers:
            worker_inventories.append({})

        available_seeds = dict(world_state.seeds)
        shed = dict(world_state.shed)
        unlocked_sheds = get_unlocked_shed_tiles(world_state.tiles)

        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))
        assigned_chore_positions = set()

        pastures_to_build = structures_to_build.get("pastures", 0) if structures_to_build else 0
        coops_to_build = structures_to_build.get("coops", 0) if structures_to_build else 0
        unfed_tiles = list(unfed_animal_tiles or [])

        # Pass 1: Stand-on chores (Instant execution at current worker tile)
        for w_idx in list(unassigned_workers):
            pos = worker_positions[w_idx]
            x, y = pos
            tile = world_state.tiles[y][x]
            inv = worker_inventories[w_idx]

            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    actions[w_idx] = ["DIG"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                elif "animal" in tile and tile.get("animal"):
                    if not tile.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                        actions[w_idx] = ["FEED"]
                        inv["WHEAT"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        if pos in unfed_tiles:
                            unfed_tiles.remove(pos)
                        continue

                    if tile.get("yield_units", 0) > 0:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if tile.get("fertilizer_available", False):
                        actions[w_idx] = ["COLLECT_FERTILIZER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if care_animals and not tile.get("cared_today", False):
                        actions[w_idx] = ["CARE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "PASTURE" and "animal" not in tile:
                    if inv.get("COW", 0) > 0:
                        actions[w_idx] = ["PLACE", "COW"]
                        inv["COW"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    elif inv.get("SHEEP", 0) > 0:
                        actions[w_idx] = ["PLACE", "SHEEP"]
                        inv["SHEEP"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "COOP" and "animal" not in tile:
                    if inv.get("GOOSE", 0) > 0:
                        actions[w_idx] = ["PLACE", "GOOSE"]
                        inv["GOOSE"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "PLANT":
                    pos_harvest = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                    if pos_harvest:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if use_fert_on_crops and tile.get("crop") == "MELON" and tile.get("fertilized_until_day", -1) < world_state.day and inv.get("FERTILIZER", 0) > 0:
                        actions[w_idx] = ["FERTILIZE"]
                        inv["FERTILIZER"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None:
                if pastures_to_build > 0:
                    actions[w_idx] = ["BUILD_PASTURE"]
                    pastures_to_build -= 1
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                elif coops_to_build > 0:
                    actions[w_idx] = ["BUILD_COOP"]
                    coops_to_build -= 1
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                elif world_state.day <= 26:
                    for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                        if available_seeds.get(sc, 0) > 0:
                            actions[w_idx] = ["PLANT", sc]
                            available_seeds[sc] -= 1
                            unassigned_workers.remove(w_idx)
                            assigned_chore_positions.add(pos)
                            break

        # Pass 2: Shed Logistics
        empty_pastures = []
        empty_coops = []
        for y in range(len(world_state.tiles)):
            for x in range(len(world_state.tiles[0])):
                t = world_state.tiles[y][x]
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE" and "animal" not in t:
                        empty_pastures.append((x, y))
                    elif t.get("kind") == "COOP" and "animal" not in t:
                        empty_coops.append((x, y))

        for w_idx in list(unassigned_workers):
            w_pos = worker_positions[w_idx]
            inv = worker_inventories[w_idx]

            if w_pos in unlocked_sheds:
                if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                    actions[w_idx] = ["PICKUP", "COW", 1]
                    shed["COW"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                    actions[w_idx] = ["PICKUP", "SHEEP", 1]
                    shed["SHEEP"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0 and empty_coops:
                    actions[w_idx] = ["PICKUP", "GOOSE", 1]
                    shed["GOOSE"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif unfed_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    take_qty = min(4, shed["WHEAT"])
                    actions[w_idx] = ["PICKUP", "WHEAT", take_qty]
                    shed["WHEAT"] -= take_qty
                    unassigned_workers.remove(w_idx)
                    continue

        # Pass 3: Targeted Spatial Routing
        claimed_unfed = set()
        for w_idx in list(unassigned_workers):
            w_pos = worker_positions[w_idx]
            inv = worker_inventories[w_idx]

            if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                if empty_pastures:
                    target = min(empty_pastures, key=lambda p: manhattan(w_pos, p))
                    actions[w_idx] = [get_next_step(w_pos, target, world_state.tiles)]
                    unassigned_workers.remove(w_idx)
                    continue
            if inv.get("GOOSE", 0) > 0:
                if empty_coops:
                    target = min(empty_coops, key=lambda p: manhattan(w_pos, p))
                    actions[w_idx] = [get_next_step(w_pos, target, world_state.tiles)]
                    unassigned_workers.remove(w_idx)
                    continue

            if inv.get("WHEAT", 0) > 0 and unfed_tiles:
                avail_unfed = [p for p in unfed_tiles if p not in claimed_unfed]
                target = min(avail_unfed or unfed_tiles, key=lambda p: manhattan(w_pos, p))
                claimed_unfed.add(target)
                actions[w_idx] = [get_next_step(w_pos, target, world_state.tiles)]
                unassigned_workers.remove(w_idx)
                continue

            if inv.get("WHEAT", 0) == 0 and unfed_tiles and shed.get("WHEAT", 0) > 0:
                if len(claimed_unfed) < len(unfed_tiles) and unlocked_sheds:
                    actions[w_idx] = [get_next_step(w_pos, unlocked_sheds[0], world_state.tiles)]
                    unassigned_workers.remove(w_idx)
                    continue

        # Pass 4: General Chores & Fallback
        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]
        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if remaining_chores:
                best_chore = None
                best_score = -999999.0
                for chore in remaining_chores:
                    dist = manhattan(w_pos, chore["pos"])
                    score = chore["weight"] - dist * 2.0
                    if score > best_score:
                        best_score = score
                        best_chore = chore

                if best_chore:
                    target_pos = best_chore["pos"]
                    remaining_chores.remove(best_chore)
                    assigned_chore_positions.add(target_pos)
                    actions[w_idx] = [get_next_step(w_pos, target_pos, world_state.tiles)]
                    continue

            if w_pos not in unlocked_sheds and unlocked_sheds:
                actions[w_idx] = [get_next_step(w_pos, unlocked_sheds[0], world_state.tiles)]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }
