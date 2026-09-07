import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import numpy as np

from scratch.test_hybrid_features import HybridCandidate
from candidates.candidate_cl_aethel_prime import _bfs

class RefinedZoningCandidate(HybridCandidate):
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        actions = [None] * len(all_workers)
        claimed_tiles = set()
        ns = self._nearest_shed(all_workers[0], tiles) if hasattr(self, '_nearest_shed') else (4, 4)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        # ── Step 1: Local-First Execution ─────────────────────────────────────
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER", "TOMATO", "CARROT"))
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in ((4, 4), (5, 4), (4, 5), (5, 5)) and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_tiles.add(pos)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    age = day - int(t.get("planted_day", 0) or 0)
                    
                    # Guarded harvest
                    if pos in scan_res["ripe_crops"] and pos not in claimed_tiles:
                        actions[i] = ["HARVEST"]
                        claimed_tiles.add(pos)
                        continue

                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_tiles:
                        actions[i] = ["FERTILIZE"]
                        claimed_tiles.add(pos)
                        continue

                    if not t.get("watered_today") and pos not in claimed_tiles:
                        actions[i] = ["WATER"]
                        claimed_tiles.add(pos)
                        continue

                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["FEED"]
                            claimed_tiles.add(pos)
                            continue
                        if not t.get("cared_today") and pos not in claimed_tiles:
                            actions[i] = ["CARE"]
                            claimed_tiles.add(pos)
                            continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_tiles:
                            actions[i] = ["HARVEST"]
                            claimed_tiles.add(pos)
                            continue
                        if t.get("fertilizer_available") and pos not in claimed_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]
                            claimed_tiles.add(pos)
                            continue
                    else:
                        sp = "SHEEP" if sheep_inv > 0 else ("COW" if cow_inv > 0 else None)
                        if sp and pos not in claimed_tiles:
                            actions[i] = ["PLACE", sp]
                            claimed_tiles.add(pos)
                            continue
                elif k == "WEED" and pos not in claimed_tiles:
                    actions[i] = ["DIG"]
                    claimed_tiles.add(pos)
                    continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_tiles:
                    actions[i] = ["BUILD_PASTURE"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]
                    claimed_tiles.add(pos)
                    continue

        # ── Step 2: Role-Based Routing ─────────────────────────────────────────
        n_workers = len(all_workers)

        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue

            produce_load = sum(int(inv.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER", "TOMATO", "CARROT"))
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            target = None

            # ROLE DEFINITIONS:
            # i == 0: Farmer (Core Corridor Leader)
            # i == 1: Herdmaster (Animal Stocker & Feeder)
            # i in (2, 3): NE Pasture team (if NE unlocked)
            # i >= 4: Field Orchard Team (SW & NW Crops)
            if i in (0, 1):
                assigned_zone = "NW"
            elif i in (2, 3) and "NE" in quads:
                assigned_zone = "NE"
            elif "SW" in quads:
                assigned_zone = "SW"
            else:
                assigned_zone = "NW"

            if tiles[pos[1]][pos[0]] == "LOCKED" and pos not in ((4, 4), (5, 4), (4, 5), (5, 5)):
                target = (4, 4)
            elif (cow_inv + sheep_inv) > 0:
                car_sp = "COW" if cow_inv > 0 else "SHEEP"
                matching_slots = [p for p in target_pasture_slots if p not in claimed_tiles]
                cands = [p for p in matching_slots if p in scan_res["empty_p"]] or [p for p in matching_slots if p in scan_res["unbuilt_p"]] or [p for p in scan_res["empty_p"] if p not in claimed_tiles] or [p for p in scan_res["unbuilt_p"] if p not in claimed_tiles]
                if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))
            elif w_inv > 0 and scan_res["hungry"]:
                cands = [h for h in scan_res["hungry"] if h not in claimed_tiles]
                if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))
            elif produce_load > 0 and (hour >= 22 or produce_load >= 5):
                target = ns

            # Herdmaster & Farmer chores
            elif i in (0, 1) or (assigned_zone in ("NW", "NE") and (scan_res["hungry"] or scan_res["empty_p"] or scan_res["unbuilt_p"])):
                has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
                if i == 1 and has_animals_in_shed and (cow_inv + sheep_inv) == 0:
                    if pos in ((4, 4), (5, 4), (4, 5), (5, 5)):
                        if int(shed.get("COW", 0) or 0) > 0: actions[i] = ["PICKUP", "COW", 1]; continue
                        elif int(shed.get("SHEEP", 0) or 0) > 0: actions[i] = ["PICKUP", "SHEEP", 1]; continue
                    else:
                        target = ns
                elif scan_res["hungry"] and w_inv == 0 and int(shed.get("WHEAT", 0) or 0) > 0:
                    if pos in ((4, 4), (5, 4), (4, 5), (5, 5)):
                        actions[i] = ["PICKUP", "WHEAT", min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))]
                        continue
                    else:
                        target = ns
                elif has_animals_in_shed and (cow_inv + sheep_inv) == 0:
                    if pos in ((4, 4), (5, 4), (4, 5), (5, 5)):
                        if int(shed.get("COW", 0) or 0) > 0: actions[i] = ["PICKUP", "COW", 1]; continue
                        elif int(shed.get("SHEEP", 0) or 0) > 0: actions[i] = ["PICKUP", "SHEEP", 1]; continue
                    else:
                        target = ns
                elif scan_res["unbuilt_p"] and has_animals_in_shed:
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))
                elif scan_res["ripe_a"]:
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

            # Crop chores
            if target is None:
                def in_z(pt):
                    if assigned_zone == "NW": return pt[0] < 5 and pt[1] < 5
                    if assigned_zone == "NE": return pt[0] >= 5 and pt[1] < 5
                    if assigned_zone == "SW": return pt[0] < 5 and pt[1] >= 5
                    return True

                if target is None and scan_res.get("urgent_unwatered"):
                    cands = [u for u in scan_res["urgent_unwatered"] if u not in claimed_tiles and in_z(u)] or [u for u in scan_res["urgent_unwatered"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("ripe_a"):
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("fert"):
                    cands = [f for f in scan_res["fert"] if f not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("ripe_crops"):
                    cands = [r for r in scan_res["ripe_crops"] if r not in claimed_tiles and in_z(r)] or [r for r in scan_res["ripe_crops"] if r not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("unwatered"):
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_tiles and in_z(u)] or [u for u in scan_res["unwatered"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("unbuilt_p"):
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("plant_s") and int(seeds.get("STRAWBERRY", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_s"] if p not in claimed_tiles and in_z(p)] or [p for p in scan_res["plant_s"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("plant_m") and int(seeds.get("MELON", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_m"] if p not in claimed_tiles and in_z(p)] or [p for p in scan_res["plant_m"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("plant_w") and int(seeds.get("WHEAT", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_w"] if p not in claimed_tiles and in_z(p)] or [p for p in scan_res["plant_w"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

                if target is None and scan_res.get("weeds"):
                    cands = [w for w in scan_res["weeds"] if w not in claimed_tiles and in_z(w)] or [w for w in scan_res["weeds"] if w not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: abs(pos[0]-p[0]) + abs(pos[1]-p[1]))

            if target is not None:
                claimed_tiles.add(target)
                mv = _bfs(pos, target, tiles)
                actions[i] = [mv] if mv != "PASS" else ["PASS"]
            else:
                actions[i] = ["PASS"]

        return actions

if __name__ == '__main__':
    print("Testing RefinedZoningCandidate across seeds 42, 100, 2024...")
    rz = RefinedZoningCandidate()
    scores = []
    for s in [42, 100, 2024]:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([lambda o, c=None: rz(o, c), starter])
        sc = env.steps[-1][0]['reward']
        scores.append(sc)
        print(f"  Seed {s}: Final Bank = ${sc:,.1f}")
    print(f"Mean Score: ${np.mean(scores):,.1f} +/- {np.std(scores):,.1f}")
