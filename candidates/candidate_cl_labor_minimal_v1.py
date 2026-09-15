# SPDX-License-Identifier: MIT
"""
Candidate: ClosedLoopLaborMinimalV1 (L_Minimal)
Parent: candidates/candidate_cl_fert_gated.py (M1) + Wheat Quota 50 (Q50)
Modifications on top of M1:
  1. Wheat Quota 50 Parent Logic (Q50):
     - Tracks total wheat planted and limits wheat seed purchases to quota 50.
     - Clamps res["plant_w"] in _scan_field() to remaining quota.
  2. Labor Bandwidth Minimal Policy (L_Minimal):
     - Safe-window urgency sorting in _scan_field():
       Prioritizes perishable/capped strawberry harvests before melon and wheat.
     - Discretionary task gating in _scan_field():
       When mature strawberries await harvest, suppresses peripheral weed clearing.
Zero movement, zoning, pasture reservation, cow timing, or market changes.
"""

import os
import sys
import copy
from collections import defaultdict, deque

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidates.candidate_cl_fert_gated as m1_module

class ClosedLoopLaborMinimalV1(m1_module.ClosedLoopEconomicV1):
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

        # 2. Safe-Window Urgency Sorting
        has_ripe_straw = False
        def crop_urgency_key(pos):
            nonlocal has_ripe_straw
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                has_ripe_straw = True
                return 0 if yu >= 2 else 5
            elif c == "MELON":
                return 10
            elif c == "WHEAT":
                return 20
            return 50
        
        res["ripe_crops"].sort(key=crop_urgency_key)
        
        # 3. Discretionary Task Gating: Suppress peripheral weed digging when ripe strawberries wait
        if has_ripe_straw:
            res["weeds"] = []
            
        return res

agent = ClosedLoopLaborMinimalV1()
def candidate_agent(obs, config=None):
    return agent(obs, config)
