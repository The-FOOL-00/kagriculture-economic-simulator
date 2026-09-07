"""
Arm D: Arm C + Zone Ownership (Z2)
Workers have strict zone assignments:
- Herders (0 & 1): Livestock corridor & shed.
- Cultivators (2-5): NW Sector.
- Cultivators (6-8): NE Sector.
- Cultivators (9-12): SW Sector.
Tasks are filtered to the worker's assigned zone first.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
from scratch.test_arm_c import ClosedLoopArmC, run_telemetry_match
from candidates.candidate_closed_loop_execution_v1 import (
    _bfs_step, _dist, _nearest_shed, SHED_ACCESS, PRODUCE_TO_DROP, BOARD, PASTURE_SPECIES
)

def _quad(x, y):
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

class ClosedLoopArmD(ClosedLoopArmC):
    def _get_worker_zone(self, worker_idx, n_workers, quads):
        if worker_idx in (0, 1):
            return "LIVESTOCK"
        elif worker_idx in (2, 3, 4, 5):
            return "NW"
        elif worker_idx in (6, 7, 8) and "NE" in quads:
            return "NE"
        elif worker_idx >= 9 and "SW" in quads:
            return "SW"
        return "NW"

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())
        n_workers = len(all_workers)

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-first execution on current tile (same as Arm C)
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                    if fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles:
                        actions[i] = ["WATER"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["FEED"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                        if not t.get("cared_today") and pos not in claimed_action_tiles:
                            actions[i] = ["CARE"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["HARVEST"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                        if t.get("fertilizer_available") and pos not in claimed_action_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                    else:
                        if cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                        elif sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]
                            claimed_action_tiles.add(pos)
                            self._worker_targets.pop(i, None)
                            continue
                elif k == "WEED" and pos not in claimed_action_tiles:
                    actions[i] = ["DIG"]
                    claimed_action_tiles.add(pos)
                    self._worker_targets.pop(i, None)
                    continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_action_tiles:
                    actions[i] = ["BUILD_PASTURE"]
                    claimed_action_tiles.add(pos)
                    self._worker_targets.pop(i, None)
                    continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]
                    claimed_action_tiles.add(pos)
                    self._worker_targets.pop(i, None)
                    continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]
                    claimed_action_tiles.add(pos)
                    self._worker_targets.pop(i, None)
                    continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]
                    claimed_action_tiles.add(pos)
                    self._worker_targets.pop(i, None)
                    continue

        # Step 2: Zone Ownership + Persistent Commitments
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue

            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            target = None
            w_zone = self._get_worker_zone(i, n_workers, quads)

            def in_zone(pt):
                if w_zone == "LIVESTOCK":
                    return pt in target_pasture_slots
                return _quad(pt[0], pt[1]) == w_zone

            # Check existing commitment
            if i in self._worker_targets:
                active_t, task_type, sc = self._worker_targets[i]
                if sc < 15 and active_t not in claimed_action_tiles:
                    ax, ay = active_t
                    at = tiles[ay][ax] if 0 <= ay < BOARD and 0 <= ax < BOARD else None
                    valid = True
                    if task_type == "WATER" and (not isinstance(at, dict) or at.get("watered_today")):
                        valid = False
                    elif task_type == "HARVEST" and (not isinstance(at, dict) or int(at.get("yield_units", 0) or 0) == 0):
                        valid = False
                    elif task_type == "FEED" and (w_inv == 0 or (isinstance(at, dict) and at.get("fed_today"))):
                        valid = False
                    elif task_type == "DROP" and produce_load == 0:
                        valid = False

                    if valid:
                        target = active_t
                        self._worker_targets[i] = (active_t, task_type, sc + 1)
                    else:
                        self._worker_targets.pop(i, None)
                else:
                    self._worker_targets.pop(i, None)

            # Replan with Zone Ownership filter
            if target is None:
                has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
                chosen_type = "MOVE"

                if (cow_inv + sheep_inv) > 0:
                    cands = [p for p in scan_res["empty_p"] if p not in claimed_action_tiles] or [p for p in scan_res["unbuilt_p"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLACE"
                elif has_animals_in_shed and (cow_inv + sheep_inv) == 0 and (i in (0, 1) or hour <= 3):
                    if pos in SHED_ACCESS:
                        if int(shed.get("COW", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "COW", 1]
                            continue
                        elif int(shed.get("SHEEP", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "SHEEP", 1]
                            continue
                    else:
                        target = ns
                        chosen_type = "PICKUP"

                if target is None and scan_res["hungry"]:
                    if w_inv > 0:
                        cands = [h for h in scan_res["hungry"] if h not in claimed_action_tiles]
                        if cands:
                            adj_cands = [h for h in cands if _dist(pos, h) == 1]
                            target = adj_cands[0] if adj_cands else min(cands, key=lambda p: _dist(pos, p))
                            chosen_type = "FEED"
                    elif int(shed.get("WHEAT", 0) or 0) > 0 and (i in (0, 1) or (w_zone == "LIVESTOCK" and hour <= 6)):
                        if pos in SHED_ACCESS:
                            batch_pickup = min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))
                            actions[i] = ["PICKUP", "WHEAT", batch_pickup]
                            continue
                        else:
                            target = ns
                            chosen_type = "PICKUP"

                if target is None and produce_load > 0 and (hour >= 20 or produce_load >= 5):
                    target = ns
                    chosen_type = "DROP"

                # Priority 1: Urgent unwatered (filter by zone first, then fallback)
                if target is None and scan_res["urgent_unwatered"]:
                    cands = [u for u in scan_res["urgent_unwatered"] if u not in claimed_action_tiles and in_zone(u)] or [u for u in scan_res["urgent_unwatered"] if u not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "WATER"

                # Priority 2: Harvest ripe animals (Herders first)
                if target is None and scan_res["ripe_a"] and (w_zone == "LIVESTOCK" or hour >= 16):
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "HARVEST"

                # Priority 3: Collect fertilizer
                if target is None and scan_res["fert"] and (w_zone == "LIVESTOCK" or hour >= 16):
                    cands = [f for f in scan_res["fert"] if f not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "COLLECT_FERT"

                # Priority 4: Harvest ripe crops (filtered by zone!)
                if target is None and scan_res["ripe_crops"]:
                    cands = [r for r in scan_res["ripe_crops"] if r not in claimed_action_tiles and in_zone(r)] or [r for r in scan_res["ripe_crops"] if r not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "HARVEST"

                # Priority 5: Crop watering (contiguous 1-step, filtered by zone!)
                if target is None and scan_res["unwatered"]:
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_action_tiles and in_zone(u)] or [u for u in scan_res["unwatered"] if u not in claimed_action_tiles]
                    if cands:
                        adj_cands = [u for u in cands if _dist(pos, u) == 1]
                        target = adj_cands[0] if adj_cands else min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "WATER"

                # Priority 6: Planting (filtered by zone!)
                if target is None and scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_s"] if p not in claimed_action_tiles and in_zone(p)] or [p for p in scan_res["plant_s"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"
                if target is None and scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_m"] if p not in claimed_action_tiles and in_zone(p)] or [p for p in scan_res["plant_m"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"
                if target is None and scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_w"] if p not in claimed_action_tiles and in_zone(p)] or [p for p in scan_res["plant_w"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"

                # Priority 7: Build pasture
                if target is None and scan_res["unbuilt_p"]:
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "BUILD_P"

                # Priority 8: Dig weeds
                if target is None and scan_res["weeds"]:
                    cands = [w for w in scan_res["weeds"] if w not in claimed_action_tiles and in_zone(w)] or [w for w in scan_res["weeds"] if w not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "DIG"

                if target is not None:
                    self._worker_targets[i] = (target, chosen_type, 1)

            if target is not None:
                claimed_action_tiles.add(target)
                actions[i] = [_bfs_step(pos, target, tiles)]
            else:
                actions[i] = ["PASS"]

        return actions

_ARM_D_AGENT = ClosedLoopArmD()
def arm_d_agent(obs, config=None):
    return _ARM_D_AGENT(obs, config)

if __name__ == "__main__":
    from scratch.test_arm_c import arm_c_agent
    print("Evaluating Arm C (+Commitment)...")
    res_c = run_telemetry_match(arm_c_agent, seed=42)
    print("Evaluating Arm D (Arm C + Zone Ownership)...")
    res_d = run_telemetry_match(arm_d_agent, seed=42)

    print("\n=== Comparative Telemetry (Seed 42) ===")
    print(f"{'Metric':<25} | {'Arm C (+Commitment)':<20} | {'Arm D (+Zone Ownership)':<22} | {'Delta':<10}")
    print("-" * 80)
    for k in ["reward", "productive", "movement", "idle", "mean_leg", "pct_1step", "pct_2step", "zone_per_w_day", "shed_per_w_day", "prod_per_move"]:
        vc = res_c[k]
        vd = res_d[k]
        diff = vd - vc
        if isinstance(vc, float):
            print(f"{k:<25} | {vc:<20.2f} | {vd:<22.2f} | {diff:+10.2f}")
        else:
            print(f"{k:<25} | {vc:<20} | {vd:<22} | {diff:+10}")
