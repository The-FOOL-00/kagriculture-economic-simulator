"""
Advanced Multi-Worker Chore Scheduling, Animal Care Coordination, and Path Optimization.
"""

from config import CROPS, ANIMALS, PRODUCTS
from pathfinding import get_next_step, manhattan, get_unlocked_shed_tiles


class WorkerScheduler:
    def __init__(self):
        pass

    def plan_hires(self, farm_state):
        """
        Compute optimal number of farm hands to hire for the day at hour 0.
        """
        day = farm_state.day
        hour = farm_state.hour
        money = farm_state.money

        if hour != 0:
            return farm_state.hires_today

        # Count active chores
        total_chores = (
            len(farm_state.weed_tiles) +
            len(farm_state.harvestable_plants) +
            len(farm_state.unwatered_plants) +
            len(farm_state.empty_tiles) +
            len(farm_state.unfed_animals) * 2 +
            len(farm_state.harvestable_animals)
        )

        unlocked_quads = len(farm_state.unlocked_quadrants)
        
        # Scaling formula based on unlocked quadrants and farm load
        if day <= 1:
            target_workers = 3  # 1 farmer + 2 hands
        elif day <= 4:
            target_workers = 4  # 1 farmer + 3 hands
        else:
            if unlocked_quads == 1:
                target_workers = min(4, max(2, (total_chores + 8) // 10))
            elif unlocked_quads == 2:
                target_workers = min(5, max(3, (total_chores + 10) // 11))
            else:
                target_workers = min(6, max(4, (total_chores + 12) // 12))

        # Check affordability
        target_hands = max(0, target_workers - 1)
        if money < 100:
            target_hands = min(2, target_hands)
        elif money < 250:
            target_hands = min(3, target_hands)

        return target_hands

    def assign_worker_actions(self, farm_state):
        """
        Generate conflict-free, high-throughput actions for all workers.
        """
        num_workers = 1 + len(farm_state.hands)
        worker_positions = [farm_state.farmer_pos] + list(farm_state.hands)
        worker_inventories = farm_state.inventories
        
        # Track available seeds for atomic PLANT safety
        available_seeds = dict(farm_state.seeds)
        unlocked_sheds = get_unlocked_shed_tiles(farm_state.tiles)
        
        # Build master chore list
        chores = []
        
        # 1. Harvests (Priority 100)
        for pos in farm_state.harvestable_plants:
            chores.append({"type": "HARVEST_PLANT", "pos": pos, "weight": 100})
        for pos in farm_state.harvestable_animals:
            chores.append({"type": "HARVEST_ANIMAL", "pos": pos, "weight": 95})

        # 2. Weeds (Priority 90)
        for pos in farm_state.weed_tiles:
            chores.append({"type": "DIG_WEED", "pos": pos, "weight": 90})

        # 3. Animal care / feeding (Priority 88)
        for pos in farm_state.fertilizer_animals:
            chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 88})
        for pos in farm_state.unfed_animals:
            chores.append({"type": "FEED_ANIMAL", "pos": pos, "weight": 87})
        for pos in farm_state.uncared_animals:
            chores.append({"type": "CARE_ANIMAL", "pos": pos, "weight": 85})

        # 4. Animal placement into empty structures
        for pos, kind in farm_state.empty_structures:
            chores.append({"type": "PLACE_ANIMAL", "pos": pos, "kind": kind, "weight": 84})

        # 5. Build coop early (Day 0-3) in NW quadrant
        num_coops = len([t for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("kind") == "COOP"])
        if farm_state.day <= 3 and num_coops < 3 and farm_state.money >= 500:
            coop_spots = [(0, 0), (0, 1), (1, 0), (1, 1)]
            for spot in coop_spots:
                if farm_state.tiles[spot[1]][spot[0]] is None:
                    chores.append({"type": "BUILD_COOP", "pos": spot, "weight": 83})
                    break

        # 6. Water plants (Priority 80)
        for pos in farm_state.unwatered_plants:
            chores.append({"type": "WATER", "pos": pos, "weight": 80})

        # 7. Plant seeds on empty tiles (Priority 70)
        total_seeds = sum(available_seeds.values())
        if total_seeds > 0 and farm_state.day <= 26:
            for pos in farm_state.empty_tiles:
                if farm_state.day <= 3 and num_coops < 3 and pos in [(0, 0), (0, 1), (1, 0)]:
                    continue
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        assigned_chore_positions = set()
        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))

        # Pass 1: Handle workers currently standing on active chore tiles
        for w_idx in list(unassigned_workers):
            pos = worker_positions[w_idx]
            x, y = pos
            tile = farm_state.tiles[y][x]
            inv = worker_inventories[w_idx] if w_idx < len(worker_inventories) else {}

            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    actions[w_idx] = ["DIG"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                if kind == "PLANT":
                    # Harvest check
                    if pos in farm_state.harvestable_plants:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Fertilize check (if worker has fertilizer in inventory)
                    if inv.get("FERTILIZER", 0) > 0 and tile.get("fertilized_until_day", -1) < farm_state.day:
                        actions[w_idx] = ["FERTILIZE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Water check
                    if not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif "animal" in tile and tile.get("animal"):
                    # Collect fertilizer
                    if tile.get("fertilizer_available", False):
                        actions[w_idx] = ["COLLECT_FERTILIZER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    # Feed animal
                    if not tile.get("fed_today", False):
                        if inv.get("WHEAT", 0) > 0:
                            actions[w_idx] = ["FEED"]
                            unassigned_workers.remove(w_idx)
                            assigned_chore_positions.add(pos)
                            continue
                    # Care animal
                    if not tile.get("cared_today", False):
                        actions[w_idx] = ["CARE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    # Harvest product
                    if tile.get("yield_units", 0) > 0:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind in ("COOP", "PASTURE") and tile.get("animal") is None:
                    if kind == "COOP" and inv.get("GOOSE", 0) > 0:
                        actions[w_idx] = ["PLACE", "GOOSE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None:
                # Coop building check
                coop_chore = [c for c in chores if c["type"] == "BUILD_COOP" and c["pos"] == pos]
                if coop_chore:
                    actions[w_idx] = ["BUILD_COOP"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                # Planting check
                if farm_state.day <= 26:
                    planted = False
                    for seed_crop in ["MELON", "CARROT", "WHEAT", "STRAWBERRY", "TOMATO"]:
                        if available_seeds.get(seed_crop, 0) > 0:
                            actions[w_idx] = ["PLANT", seed_crop]
                            available_seeds[seed_crop] -= 1
                            unassigned_workers.remove(w_idx)
                            assigned_chore_positions.add(pos)
                            planted = True
                            break
                    if planted:
                        continue

        # Pass 2: Handle shed pickup actions (Wheat for feeding, Goose for coops)
        for w_idx in list(unassigned_workers):
            w_pos = worker_positions[w_idx]
            inv = worker_inventories[w_idx] if w_idx < len(worker_inventories) else {}

            if w_pos in unlocked_sheds:
                # If coops need animals and shed has Goose
                if farm_state.empty_structures and farm_state.shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0:
                    actions[w_idx] = ["PICKUP", "GOOSE", 1]
                    unassigned_workers.remove(w_idx)
                    continue
                # If animals need feed and worker has 0 wheat, pickup wheat from shed
                if farm_state.unfed_animals and farm_state.shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    pickup_amount = min(5, farm_state.shed["WHEAT"])
                    actions[w_idx] = ["PICKUP", "WHEAT", pickup_amount]
                    unassigned_workers.remove(w_idx)
                    continue

        # Pass 3: Route remaining workers towards best available chores
        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]

        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if not remaining_chores:
                # Move to shed if far, otherwise PASS
                if w_pos not in unlocked_sheds:
                    move = get_next_step(w_pos, unlocked_sheds[0], farm_state.tiles)
                    actions[w_idx] = [move]
                else:
                    actions[w_idx] = ["PASS"]
                continue

            # Greedy best chore selection
            best_chore = None
            best_score = -999999
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
                
                move = get_next_step(w_pos, target_pos, farm_state.tiles)
                actions[w_idx] = [move]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }
