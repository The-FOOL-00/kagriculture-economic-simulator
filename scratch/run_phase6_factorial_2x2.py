import sys
import os
import json
import numpy as np
import scipy.stats as stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Arm X: Q50 wheat expansion + original Q50 cow timing + no reservation (Raw Quota 50)
class ArmX(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

# Arm W: Q50 wheat expansion + M1 cow timing + no reservation (Cap Day 6 cow buy at 1)
class ArmW(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if day == 6:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    new_orders.append(["BUY_ANIMAL", "COW", min(1, int(o[2]))])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Arm Z: Q50 wheat expansion + Q50 cow timing + reservation (Mechanism A: NW cow cap 4)
class ArmZ(ParameterizedQuotaAgent):
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

# Arm Y: Q50 wheat expansion + M1 cow timing + reservation (Cap Day 6 at 1 + NW cow cap 4)
class ArmY(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        new_orders = []
        for o in orders:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                allowed = int(o[2])
                if day == 6:
                    allowed = min(allowed, 1)
                if len(quads) == 1:
                    allowed = min(allowed, max(0, 4 - total_c))
                if allowed > 0:
                    new_orders.append(["BUY_ANIMAL", "COW", allowed])
            else:
                new_orders.append(o)
        return new_orders

def run_2x2_seed(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_one(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        sold = {"WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0}
        for st in steps:
            for o in (st[0].get("action") or {}).get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    if o[1] in sold: sold[o[1]] += int(o[2])
        return {
            "reward": steps[-1][0]["reward"],
            "sold": sold
        }

    res_x = run_one(ArmX(50))
    res_w = run_one(ArmW(50))
    res_z = run_one(ArmZ(50))
    res_y = run_one(ArmY(50))

    return {
        "seed": seed,
        "X": res_x,
        "W": res_w,
        "Z": res_z,
        "Y": res_y
    }

def main():
    seeds = list(range(1050, 1150)) # 100 validation seeds
    print(f"Running Phase 6 2x2 Factorial on {len(seeds)} validation seeds (1050-1149)...")
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_2x2_seed, seeds))

    with open("scratch/phase6_factorial_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Phase 6 2x2 factorial run complete. Saved to scratch/phase6_factorial_results.json.")

if __name__ == "__main__":
    main()
