"""
Arm E / Phase 6: Short-Horizon Lookahead Study on Top of Persistent Commitments
Tests:
H0  = 0-turn lookahead (pure Euclidean/Manhattan distance)
H5  = 5-turn lookahead (immediate cluster radius 1)
H10 = 10-turn lookahead (cluster radius 2 with decay)
H20 = 20-turn lookahead (cluster radius 3 with decay)
H40 = 40-turn lookahead (cluster radius 4 with decay)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
from scratch.test_arm_c import ClosedLoopArmC, run_telemetry_match
from candidates.candidate_closed_loop_execution_v1 import (
    _bfs_step, _dist, _nearest_shed, SHED_ACCESS, PRODUCE_TO_DROP, BOARD, PASTURE_SPECIES
)

class ClosedLoopLookahead(ClosedLoopArmC):
    def __init__(self, horizon="H10"):
        super().__init__()
        self.horizon = horizon

    def _cluster_lookahead_score(self, target, candidates, base_pos):
        d = _dist(base_pos, target)
        if self.horizon == "H0":
            return -d

        tx, ty = target
        cluster_bonus = 0.0
        
        # Define max lookahead radius
        if self.horizon == "H5":
            max_r = 1
        elif self.horizon == "H10":
            max_r = 2
        elif self.horizon == "H20":
            max_r = 3
        elif self.horizon == "H40":
            max_r = 4
        else:
            max_r = 2

        for cx, cy in candidates:
            if (cx, cy) == target:
                continue
            cd = abs(tx - cx) + abs(ty - cy)
            if 1 <= cd <= max_r:
                cluster_bonus += (max_r - cd + 1) / max_r

        return -d + 0.5 * cluster_bonus

    def _pick_best_candidate(self, cands, base_pos):
        if not cands: return None
        if self.horizon == "H0":
            return min(cands, key=lambda p: _dist(base_pos, p))
        adj = [c for c in cands if _dist(base_pos, c) == 1]
        if adj:
            return adj[0]
        return max(cands, key=lambda p: self._cluster_lookahead_score(p, cands, base_pos))

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-first execution on current tile
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

        # Step 2: Persistent Commitment + Lookahead
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue

            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            target = None

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
                    elif int(shed.get("WHEAT", 0) or 0) > 0 and (i in (0, 1, 2, 3) or hour <= 6):
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

                if target is None and scan_res["urgent_unwatered"]:
                    cands = [u for u in scan_res["urgent_unwatered"] if u not in claimed_action_tiles]
                    if cands:
                        target = self._pick_best_candidate(cands, pos)
                        chosen_type = "WATER"

                if target is None and scan_res["ripe_a"]:
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "HARVEST"

                if target is None and scan_res["fert"]:
                    cands = [f for f in scan_res["fert"] if f not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "COLLECT_FERT"

                if target is None and scan_res["ripe_crops"]:
                    cands = [r for r in scan_res["ripe_crops"] if r not in claimed_action_tiles]
                    if cands:
                        target = self._pick_best_candidate(cands, pos)
                        chosen_type = "HARVEST"

                if target is None and scan_res["unwatered"]:
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_action_tiles]
                    if cands:
                        target = self._pick_best_candidate(cands, pos)
                        chosen_type = "WATER"

                if target is None and scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_s"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"
                if target is None and scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_m"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"
                if target is None and scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_w"] if p not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "PLANT"

                if target is None and scan_res["unbuilt_p"]:
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_action_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                        chosen_type = "BUILD_P"

                if target is None and scan_res["weeds"]:
                    cands = [w for w in scan_res["weeds"] if w not in claimed_action_tiles]
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

if __name__ == "__main__":
    horizons = ["H0", "H5", "H10", "H20", "H40"]
    test_seeds = [42, 101, 215]
    print("=== Phase 6: Lookahead Horizon Comparison ===")
    for h in horizons:
        agent_inst = ClosedLoopLookahead(horizon=h)
        rewards = []
        moves = []
        legs = []
        pct1s = []
        for s in test_seeds:
            res = run_telemetry_match(lambda obs, cfg=None: agent_inst(obs, cfg), seed=s)
            rewards.append(res["reward"])
            moves.append(res["movement"])
            legs.append(res["mean_leg"])
            pct1s.append(res["pct_1step"])
        import numpy as np
        print(f"Horizon {h:<4}: Reward={np.mean(rewards):9.1f} | Moves={np.mean(moves):6.1f} | Mean Leg={np.mean(legs):4.2f} | 1-step%={np.mean(pct1s):4.1f}%")
