# SPDX-License-Identifier: MIT
"""
Research Candidate: ResearchBOnlyV1 (B_Only)
Parent: candidates/candidate_cl_fert_gated.py (M1) + Wheat Quota 50 (Q50)
Modifications on top of Raw Q50:
  1. Component B ONLY (Discretionary Weed Task Gating):
     When ripe strawberries exist in res["ripe_crops"], suppress peripheral weed digging
     by clearing res["weeds"] = [].
  2. ABSOLUTELY NO COMPONENT A:
     Zero urgency sorting.
     res["ripe_crops"] maintains exact natural spatial coordinate order from M1.
Zero movement, zoning, pasture reservation, cow timing, crop priority, or market changes.
"""

import os
import sys
import copy
from collections import defaultdict, deque

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidates.candidate_cl_fert_gated as m1_module

class ResearchBOnlyV1(m1_module.ClosedLoopEconomicV1):
    def __init__(self, quota=50):
        super().__init__()
        self.quota = quota
        self.total_wheat_planted = 0
        self.known_wheat_tiles = set()

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        if step == 0 or step <= self._step:
            self.total_wheat_planted = 0
            self.known_wheat_tiles.clear()

        p = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm = farms[p] if p < len(farms) else {}
        tiles = farm.get("tiles") or []

        curr_wheat = set()
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if isinstance(t, dict) and t.get("crop") == "WHEAT":
                    curr_wheat.add((c, r))
        new_wheat = curr_wheat - self.known_wheat_tiles
        self.total_wheat_planted += len(new_wheat)
        self.known_wheat_tiles = curr_wheat

        return super().__call__(obs, config)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        wheat_s = int(seeds.get("WHEAT", 0) or 0)
        rem = max(0, self.quota - (self.total_wheat_planted + wheat_s))
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # Replace default wheat seed buy with quota-scaled buy
        new_orders = []
        for o in orders:
            if isinstance(o, list) and len(o) >= 2 and o[0] == "BUY_SEED" and o[1] == "WHEAT":
                can_buy = min(int(o[2]), rem)
                if can_buy > 0:
                    new_orders.append(["BUY_SEED", "WHEAT", can_buy])
            else:
                new_orders.append(o)

        # Allow wheat buffer expansion if quota permits
        if hour == 0 and 2 <= day <= 24 and rem > 0 and len(new_orders) < 8:
            target_buf = min(rem + wheat_s, 25 if day <= 18 else 12)
            if wheat_s < target_buf and money >= 180:
                can_buy_w = min(target_buf - wheat_s, min(15, int((money - 120) // 10)))
                can_buy_w = min(can_buy_w, rem)
                if can_buy_w > 0:
                    has_w = any(o[0] == "BUY_SEED" and o[1] == "WHEAT" for o in new_orders)
                    if not has_w:
                        new_orders.append(["BUY_SEED", "WHEAT", can_buy_w])

        return new_orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # 1. Wheat Quota Clamp on planting candidates
        rem = max(0, self.quota - self.total_wheat_planted)
        if len(res["plant_w"]) > rem:
            res["plant_w"] = res["plant_w"][:rem]

        # 2. Component B ONLY: Discretionary Weed Task Gating
        # Suppress peripheral weed digging when ripe strawberries await harvest.
        # res["ripe_crops"] order is 100% UNTOUCHED (zero urgency sorting).
        has_ripe_straw = any(
            isinstance(tiles[pos[1]][pos[0]], dict) and tiles[pos[1]][pos[0]].get("crop") == "STRAWBERRY"
            for pos in res["ripe_crops"]
        )
        if has_ripe_straw:
            res["weeds"] = []
            
        return res

agent = ResearchBOnlyV1()
def candidate_agent(obs, config=None):
    return agent(obs, config)
