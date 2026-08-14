"""
Grandmaster Multi-Worker Coordination: Dedicated Animal Ranch Hub + Crop Care + Fertilizer Acceleration.
"""

from config import CROPS, ANIMALS, PRODUCTS
from pathfinding import get_next_step, manhattan, get_unlocked_shed_tiles

# Structure layout reserved in NW quadrant:
# Coops at: (0,0), (0,1), (0,2), (1,0), (1,1), (1,2) [6 coops]
# Pastures at: (2,0), (2,1), (2,2), (3,0) [4 pastures]
COOP_SPOTS = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
PASTURE_SPOTS = [(2, 0), (2, 1), (2, 2), (3, 0)]
RANCH_SPOTS = set(COOP_SPOTS + PASTURE_SPOTS)


class GrandmasterScheduler:
    def __init__(self):
        pass

    def plan_hires(self, farm_state):
        day = farm_state.day
        hour = farm_state.hour
        money = farm_state.money

        if hour != 0:
            return farm_state.hires_today

        total_chores = (
            len(farm_state.weed_tiles) +
            len(farm_state.harvestable_plants) +
            len(farm_state.unwatered_plants) +
            len(farm_state.empty_tiles) +
            len(farm_state.unfed_animals) * 2 +
            len(farm_state.harvestable_animals) +
            len(farm_state.fertilizer_animals)
        )

        unlocked_quads = len(farm_state.unlocked_quadrants)
        
        if day <= 1:
            target_workers = 3
        elif day <= 4:
            target_workers = 4
        else:
            if unlocked_quads == 1:
                target_workers = min(4, max(2, (total_chores + 8) // 10))
            elif unlocked_quads == 2:
                target_workers = min(5, max(3, (total_chores + 10) // 11))
            else:
                target_workers = min(6, max(4, (total_chores + 12) // 12))

        target_hands = max(0, target_workers - 1)
        if money < 100:
            target_hands = min(2, target_hands)
        elif money < 250:
            target_hands = min(3, target_hands)

        return target_hands

    def assign_worker_actions(self, farm_state):
        num_workers = 1 + len(farm_state.hands)
        worker_positions = [farm_state.farmer_pos] + list(farm_state.hands)
        worker_inventories = farm_state.inventories
        
        available_seeds = dict(farm_state.seeds)
        unlocked_sheds = get_unlocked_shed_tiles(farm_state.tiles)
        
        chores = []
        
        # 1. Harvests (Priority 100)
        for pos in farm_state.harvestable_plants:
            chores.append({"type": "HARVEST_PLANT", "pos": pos, "weight": 100})
        for pos in farm_state.harvestable_animals:
            chores.append({"type": "HARVEST_ANIMAL", "pos": pos, "weight": 98})

        # 2. Weeds (Priority 95)
        for pos in farm_state.weed_tiles:
            chores.append({"type": "DIG_WEED", "pos": pos, "weight": 95})

        # 3. Animal care / feeding (Priority 90)
        for pos in farm_state.fertilizer_animals:
            chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 92})
        for pos in farm_state.unfed_animals:
            chores.append({"type": "FEED_ANIMAL", "pos": pos, "weight": 90})
        for pos in farm_state.uncared_animals:
            chores.append({"type": "CARE_ANIMAL", "pos": pos, "weight": 88})

        # 4. Animal placement
        for pos, kind in farm_state.empty_structures:
            chores.append({"type": "PLACE_ANIMAL", "pos": pos, "kind": kind, "weight": 86})

        # 5. Build Coops & Pastures on designated ranch spots
        if farm_state.day <= 6:
            for spot in COOP_SPOTS:
                t = farm_state.tiles[spot[1]][spot[0]]
                if t is None:
                    chores.append({"type": "BUILD_COOP", "pos": spot, "weight": 85})
            for spot in PASTURE_SPOTS:
                t = farm_state.tiles[spot[1]][spot[0]]
                if t is None:
                    chores.append({"type": "BUILD_PASTURE", "pos": spot, "weight": 84})

        # 6. Water plants (Priority 80)
        for pos in farm_state.unwatered_plants:
            chores.append({"type": "WATER", "pos": pos, "weight": 80})

        # 7. Plant seeds on empty non-ranch tiles (Priority 70)
        total_seeds = sum(available_seeds.values())
        if total_seeds > 0 and farm_state.day <= 26:
            for pos in farm_state.empty_tiles:
                if farm_state.day <= 6 and pos in RANCH_SPOTS:
                    continue
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        assigned_chore_positions = set()
        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))

        # Pass 1: Workers currently standing on active chore tiles
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
                    if pos in farm_state.harvestable_plants:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Fertilize if worker has fertilizer
                    if inv.get("FERTILIZER", 0) > 0 and tile.get("fertilized_until_day", -1) < farm_state.day:
                        actions[w_idx] = ["FERTILIZE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif "animal" in tile and tile.get("animal"):
                    if tile.get("fertilizer_available", False):
                        actions[w_idx] = ["COLLECT_FERTILIZER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    if not tile.get("fed_today", False):
                        if inv.get("WHEAT", 0) > 0:
                            actions[w_idx] = ["FEED"]
                            unassigned_workers.remove(w_idx)
                            assigned_chore_positions.add(pos)
                            continue
                    if not tile.get("cared_today", False):
                        actions[w_idx] = ["CARE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    if tile.get("yield_units", 0) > 0:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "COOP" and tile.get("animal") is None:
                    if inv.get("GOOSE", 0) > 0:
                        actions[w_idx] = ["PLACE", "GOOSE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "PASTURE" and tile.get("animal") is None:
                    if inv.get("SHEEP", 0) > 0:
                        actions[w_idx] = ["PLACE", "SHEEP"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    elif inv.get("COW", 0) > 0:
                        actions[w_idx] = ["PLACE", "COW"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None:
                # Structure building
                if pos in COOP_SPOTS and farm_state.day <= 6:
                    actions[w_idx] = ["BUILD_COOP"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                if pos in PASTURE_SPOTS and farm_state.day <= 6:
                    actions[w_idx] = ["BUILD_PASTURE"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                # Planting on non-ranch tiles
                if farm_state.day <= 26:
                    if farm_state.day <= 6 and pos in RANCH_SPOTS:
                        pass
                    else:
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

        # Pass 2: Shed pickups (Wheat for animals, Animals for empty structures, Fertilizer for crops)
        for w_idx in list(unassigned_workers):
            w_pos = worker_positions[w_idx]
            inv = worker_inventories[w_idx] if w_idx < len(worker_inventories) else {}

            if w_pos in unlocked_sheds:
                # 1. Animal pickup if empty structures exist
                has_empty_coop = any(kind == "COOP" for p, kind in farm_state.empty_structures)
                has_empty_pasture = any(kind == "PASTURE" for p, kind in farm_state.empty_structures)

                if has_empty_coop and farm_state.shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0:
                    actions[w_idx] = ["PICKUP", "GOOSE", 1]
                    unassigned_workers.remove(w_idx)
                    continue
                if has_empty_pasture and farm_state.shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0:
                    actions[w_idx] = ["PICKUP", "SHEEP", 1]
                    unassigned_workers.remove(w_idx)
                    continue

                # 2. Wheat pickup for animal feeding
                if farm_state.unfed_animals and farm_state.shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    pickup_amt = min(8, farm_state.shed["WHEAT"])
                    actions[w_idx] = ["PICKUP", "WHEAT", pickup_amt]
                    unassigned_workers.remove(w_idx)
                    continue

                # 3. Fertilizer pickup if available and unfertilized melon crops exist
                if farm_state.shed.get("FERTILIZER", 0) > 0 and inv.get("FERTILIZER", 0) == 0:
                    unfert_crops = [p for p, t in farm_state.plants if t.get("crop") == "MELON" and t.get("fertilized_until_day", -1) < farm_state.day]
                    if unfert_crops:
                        actions[w_idx] = ["PICKUP", "FERTILIZER", min(2, farm_state.shed["FERTILIZER"])]
                        unassigned_workers.remove(w_idx)
                        continue

        # Pass 3: Route remaining workers towards best available chores
        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]

        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if not remaining_chores:
                if w_pos not in unlocked_sheds:
                    move = get_next_step(w_pos, unlocked_sheds[0], farm_state.tiles)
                    actions[w_idx] = [move]
                else:
                    actions[w_idx] = ["PASS"]
                continue

            best_chore = None
            best_score = -999999
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
                
                move = get_next_step(w_pos, target_pos, farm_state.tiles)
                actions[w_idx] = [move]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }
