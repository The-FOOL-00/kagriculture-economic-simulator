import sys
import os
import json
from collections import defaultdict
import numpy as np
import scipy.stats as stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Base Q50 Agent
# Counterfactual A1: Protect opening two sheep slots only ((4,2) and (2,4) in NW)
# When len(quads) == 1, cows are capped at 4.
class CounterfactualA1Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if len(quads) == 1:
            cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
            cows_shed = int(shed.get("COW", 0) or 0)
            total_c = cows_f + cows_inv + cows_shed
            
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Counterfactual A2: Protect ALL current M1 sheep-designated slots across all quadrants
# A cow cannot be bought if total cows would exceed unlocked cow-designated slots.
class CounterfactualA2Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # Count unlocked cow slots
        unlocked_cow_slots = sum(
            1 for pos in m1_module.PASTURE_SLOTS 
            if m1_module._quad(pos[0], pos[1]) in quads and m1_module.PASTURE_SPECIES.get(pos) == "COW"
        )
        
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed
        
        new_orders = []
        for o in orders:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                allowed = max(0, unlocked_cow_slots - total_c)
                can_buy = min(int(o[2]), allowed)
                if can_buy > 0:
                    new_orders.append(["BUY_ANIMAL", "COW", can_buy])
            else:
                new_orders.append(o)
        return new_orders

# Counterfactual A3: Capacity-based gating (no static species coordinates)
# Do not allow any cow purchase when purchasing that cow would make the currently available
# shared pasture capacity insufficient for all already-purchased + immediately-expected sheep.
class CounterfactualA3Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # Total unlocked pasture capacity from PASTURE_SLOTS
        total_unlocked_pastures = sum(
            1 for pos in m1_module.PASTURE_SLOTS 
            if m1_module._quad(pos[0], pos[1]) in quads
        )
        
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        sheep_shed = int(shed.get("SHEEP", 0) or 0)
        total_s = sheep_f + sheep_inv + sheep_shed

        # Expected sheep needed:
        # Before Day 9, farm must reserve capacity for at least 4 sheep (1 existing + 3 Day-9 expansion)
        # On/after Day 9, target is 6 sheep.
        expected_sheep_demand = 4 if day < 9 else 6
        needed_sheep_slots = max(total_s, expected_sheep_demand)
        
        # Max cows allowed = total_unlocked_pastures - needed_sheep_slots
        max_allowed_cows = max(0, total_unlocked_pastures - needed_sheep_slots)
        
        new_orders = []
        for o in orders:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                allowed = max(0, max_allowed_cows - total_c)
                can_buy = min(int(o[2]), allowed)
                if can_buy > 0:
                    new_orders.append(["BUY_ANIMAL", "COW", can_buy])
            else:
                new_orders.append(o)
        return new_orders

def evaluate_match_arms(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_arm(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        sold = defaultdict(int)
        sheep_shed_days = 0
        cow_shed_days = 0
        worker_moves = 0
        worker_idles = 0
        conflicts = 0 # cow placed on sheep slot
        
        for s_idx in range(len(steps)):
            p0 = steps[s_idx][0]
            obs = p0.get("observation") or {}
            act = p0.get("action") or {}
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            
            if s_idx % 24 == 23:
                sheep_shed_days += int(shed.get("SHEEP", 0) or 0)
                cow_shed_days += int(shed.get("COW", 0) or 0)

            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    sold[o[1]] += int(o[2])

            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            for wa in w_acts:
                if isinstance(wa, list) and len(wa) > 0:
                    if wa[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                        worker_moves += 1
                    elif wa[0] == "PASS":
                        worker_idles += 1
                    elif wa[0] == "PLACE" and len(wa) >= 2 and wa[1] == "COW":
                        # check if placed on sheep slot
                        pass

        farm = (steps[-1][0]["observation"].get("farms") or [{}])[0]
        tiles = farm.get("tiles") or []
        cow_count = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_count = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")

        # Pasture conflicts at end of game
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("animal") == "COW":
                    if m1_module.PASTURE_SPECIES.get((x, y)) == "SHEEP":
                        conflicts += 1

        return {
            "reward": steps[-1][0]["reward"],
            "sold": dict(sold),
            "cow_count": cow_count,
            "sheep_count": sheep_count,
            "sheep_shed_days": sheep_shed_days,
            "cow_shed_days": cow_shed_days,
            "worker_moves": worker_moves,
            "worker_idles": worker_idles,
            "conflicts": conflicts
        }

    m1_res = run_arm(m1_module.ClosedLoopEconomicV1())
    q50_res = run_arm(ParameterizedQuotaAgent(50))
    a1_res = run_arm(CounterfactualA1Agent(50))
    a2_res = run_arm(CounterfactualA2Agent(50))
    a3_res = run_arm(CounterfactualA3Agent(50))

    return {
        "seed": seed,
        "m1": m1_res,
        "q50": q50_res,
        "a1": a1_res,
        "a2": a2_res,
        "a3": a3_res
    }

def main():
    seeds = list(range(1000, 1050)) # 50 matched seeds
    print(f"Running Phase 3 Counterfactuals (A1, A2, A3) across {len(seeds)} seeds...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(evaluate_match_arms, seeds))

    with open("scratch/phase3_counterfactuals_50seeds.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Phase 3 evaluation complete. Saved to scratch/phase3_counterfactuals_50seeds.json.")

if __name__ == "__main__":
    main()
