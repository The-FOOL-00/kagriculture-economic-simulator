"""
Phase 2: Terminal Land Multiplexing Variants
============================================
Tests the independent effect of converting vacated crop plots on Days 25-27
into a final wheat production wave, keeping baseline livestock and strawberry
timing unchanged:
- Variant 2A: Baseline (No terminal wheat; wheat buying stops at Day 24)
- Variant 2B: Conservative Terminal Wheat (Buy up to 10 wheat seeds on Days 25-26)
- Variant 2C: Full Available-Plot Wheat (Buy up to 25 wheat seeds on Days 25-26)
- Variant 2D: Full Available-Plot Wheat with Synchronized Irrigation & Day-30 Harvest
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import (
    ClosedLoopEconomicV1, BOARD, TPD, SHED_ACCESS, _dist, _quad,
    _bfs_step, _nearest_shed, min_cost_bipartite_matching
)

class BaseTerminalWheatCandidate(ClosedLoopEconomicV1):
    def __init__(self, mode="none"):
        super().__init__()
        self.mode = mode # "none", "conservative", "full", "optimized"

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)

        # Terminal Wheat Buying Surge on Days 25-26
        if self.mode != "none" and hour == 0 and 25 <= day <= 26 and len(orders) < 8:
            max_target = 10 if self.mode == "conservative" else 25
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            needed_w = max(0, max_target - wheat_s)
            if needed_w > 0 and money >= 100:
                can_buy_w = min(needed_w, min(15, int((money - 50) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        if self.mode in ("full", "optimized") and day >= 25:
            # Sort weeds and vacant plots to aggressively plant terminal wheat
            plant_w = scan.get("plant_w", [])
            weeds = scan.get("weeds", [])
            if plant_w:
                # Prioritize planting wheat on plots close to shed/center for easy watering
                plant_w.sort(key=lambda p: _dist(p, (4, 4)))
                scan["plant_w"] = plant_w
        return scan

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        if self.mode != "optimized" or day < 25:
            return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        # Optimized dispatch for terminal days:
        # Prioritize digging weeds on days 25-26 to open land, planting wheat,
        # watering terminal wheat on days 26-29, and harvesting on day 30 before step 712!
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-first actions
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER"))
            w_inv = int(inv.get("WHEAT", 0) or 0)
            
            if pos in SHED_ACCESS and (produce_load > 0 or (day >= 29 and w_inv > 0)):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles and day <= 29:
                        actions[i] = ["WATER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["FEED"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if not t.get("cared_today") and pos not in claimed_action_tiles:
                            actions[i] = ["CARE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if t.get("fertilizer_available") and pos not in claimed_action_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "WEED" and pos not in claimed_action_tiles and day <= 26:
                    actions[i] = ["DIG"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
            elif t is None:
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_action_tiles and day <= 27:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

        # Delegate remaining to super's bipartite matcher
        unassigned_indices = [i for i, a in enumerate(actions) if a is None]
        if not unassigned_indices:
            return actions

        # Fallback to standard dispatch for unassigned workers
        std_acts = super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)
        for i in unassigned_indices:
            actions[i] = std_acts[i]
        return actions

class Variant2A_NoTerminalWheat(BaseTerminalWheatCandidate):
    def __init__(self): super().__init__("none")

class Variant2B_ConservativeTerminalWheat(BaseTerminalWheatCandidate):
    def __init__(self): super().__init__("conservative")

class Variant2C_FullTerminalWheat(BaseTerminalWheatCandidate):
    def __init__(self): super().__init__("full")

class Variant2D_OptimizedTerminalWheat(BaseTerminalWheatCandidate):
    def __init__(self): super().__init__("optimized")
