import sys
import os
import copy
from collections import defaultdict, deque
import numpy as np

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from candidates.candidate_cl_fert_gated import (
    BOARD, TPD, SHED_ACCESS, WELL_ACCESS, CROPS_DEF, PASTURE_SLOTS, PASTURE_SPECIES,
    MELON_TILES_D0, MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE, PRODUCE_TO_DROP,
    BASE_PRICES, MOVES, _dist, _quad, _walkable, _bfs_step, _nearest_shed,
    min_cost_bipartite_matching
)
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# L1: Reserve at least 1 worker for mature strawberry harvest
class L1_ReserveOneWorkerAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # Identify ripe strawberries
        ripe_straw = [p for p in scan_res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if not ripe_straw:
            return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        # Reserve worker 0 (farmer) or nearest worker for strawberry harvest
        target_sb = ripe_straw[0]
        chosen_w = min(range(len(all_workers)), key=lambda w: _dist(all_workers[w], target_sb))

        # Run normal dispatch
        actions = super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        # Force chosen worker towards target_sb
        w_pos = all_workers[chosen_w]
        if w_pos == target_sb:
            actions[chosen_w] = ["HARVEST"]
        else:
            actions[chosen_w] = [_bfs_step(w_pos, target_sb, tiles)]
        self._worker_targets[chosen_w] = (target_sb, "HARVEST_STRAW", 1)

        return actions

# L2: Reserve enough workers to harvest all currently mature strawberries within safe window
class L2_ReserveAllStrawberryCapacityAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        ripe_straw = [p for p in scan_res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if not ripe_straw:
            return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        actions = super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        # Guarantee up to K workers are assigned to the K ripe strawberries
        assigned_cands = set()
        for cand in ripe_straw:
            uncommitted = [w for w in range(len(all_workers)) if w not in assigned_cands]
            if not uncommitted:
                break
            best_w = min(uncommitted, key=lambda w: _dist(all_workers[w], cand))
            assigned_cands.add(best_w)
            w_pos = all_workers[best_w]
            if w_pos == cand:
                actions[best_w] = ["HARVEST"]
            else:
                actions[best_w] = [_bfs_step(w_pos, cand, tiles)]
            self._worker_targets[best_w] = (cand, "HARVEST_STRAW", 1)

        return actions

# L3: Prioritize any crop whose remaining safe harvest window is below X hours (e.g. X=24h)
class L3_SafeWindowUrgencyAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50, safe_window_thresh=24):
        super().__init__(quota)
        self.safe_window_thresh = safe_window_thresh

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Sort ripe_crops by safe window: Strawberry decays fastest, Melon next, Wheat last
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                # Strawberry capped at 4 or batching at 2
                return 0 if yu >= 2 else 5
            elif c == "MELON":
                return 10
            elif c == "WHEAT":
                return 20
            return 50
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# L4: Calculate dynamic economic urgency dispatch
class L4_EconomicUrgencyAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)

        if hour == 0:
            self._worker_targets.clear()

        # Local execution
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    can_fert = False
                    if crop == "STRAWBERRY":
                        p_day = int(t.get("planted_day", 0) or 0)
                        can_fert = (p_day + 7 <= day <= min(29, p_day + 15))
                    elif crop != "WHEAT":
                        can_fert = True
                    if can_fert and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles:
                        actions[i] = ["WATER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "PASTURE" and t.get("animal"):
                    if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                        actions[i] = ["FEED"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if not t.get("cared_today") and pos not in claimed_action_tiles:
                        actions[i] = ["CARE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

        unassigned = [w for w in range(len(all_workers)) if actions[w] is None]
        if not unassigned:
            return actions

        # Build dynamic urgency candidates: (cand_pos, pool_name, urgency_score)
        urgent_cands = []
        for p in scan_res["urgent_unwatered"]:
            urgent_cands.append((p, "URGENT_WATER", 25.0))
        
        ripe_straw = [p for p in scan_res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        for p in ripe_straw:
            urgent_cands.append((p, "HARVEST_STRAW", 20.0))

        for p in scan_res["ripe_a"]:
            urgent_cands.append((p, "RIPE_ANIMAL", 15.0))

        ripe_other = [p for p in scan_res["ripe_crops"] if p not in ripe_straw]
        for p in ripe_other:
            urgent_cands.append((p, "HARVEST_OTHER", 8.0))

        for p in scan_res["unwatered"]:
            urgent_cands.append((p, "WATER_CROPS", 6.0))

        for p in (scan_res["plant_s"] if int(seeds.get("STRAWBERRY", 0) or 0) > 0 else []):
            urgent_cands.append((p, "PLANT_STRAW", 4.0))

        for p in scan_res["unbuilt_p"]:
            urgent_cands.append((p, "UNBUILT_P", 1.5))

        for p in scan_res["weeds"]:
            urgent_cands.append((p, "WEEDS", 0.5))

        # Sort candidates by urgency descending
        urgent_cands.sort(key=lambda item: item[2], reverse=True)

        assigned_workers = set()
        for cand, name, score in urgent_cands:
            if cand in claimed_action_tiles:
                continue
            avail_workers = [w for w in unassigned if w not in assigned_workers]
            if not avail_workers:
                break
            best_w = min(avail_workers, key=lambda w: _dist(all_workers[w], cand) - (score * 0.1))
            claimed_action_tiles.add(cand)
            assigned_workers.add(best_w)
            w_pos = all_workers[best_w]
            actions[best_w] = [_bfs_step(w_pos, cand, tiles)]
            self._worker_targets[best_w] = (cand, name, 1)

        for w in unassigned:
            if w not in assigned_workers:
                actions[w] = ["PASS"]

        return actions

# L5: Opportunity-cost gating: strictly prohibit construction/clearing whenever high-value tasks pending
class L5_OpportunityCostGatingAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Check if high-value tasks exist: ripe crops or unwatered crops
        high_value_backlog = len(res["ripe_crops"]) + len(res["urgent_unwatered"]) + len(res["ripe_a"])
        if high_value_backlog > 0:
            # Gating: Suppress unbuilt_p and weeds
            res["unbuilt_p"] = []
            res["weeds"] = []
        return res
