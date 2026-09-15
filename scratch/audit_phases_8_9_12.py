import sys
import os
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

# Phase 9: Cow timing variants on M1 (WITHOUT wheat expansion)
# Baseline M1 has:
# if cows_needed > 0 and money >= 650 and len(orders) < 8:
#     can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))

class M1CowTimingVariant(m1_module.ClosedLoopEconomicV1):
    def __init__(self, mode="base"):
        super().__init__()
        self.mode = mode # "day5", "force1_d6", "force2_d6", "day7"

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        if self.mode == "day5":
            # Allow cow purchase on day 5 if money >= 650
            orders = []
            cur_m = money
            if day == 5 and hour == 0:
                cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
                cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
                cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
                cows_needed = max(0, 8 - cows_tot)
                if cows_needed > 0 and cur_m >= 650:
                    can_buy_c = min(cows_needed, min(2, int((cur_m - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        cur_m -= can_buy_c * 400
            base_orders = super()._macro_market(step, day, hour, cur_m, quads, tiles, shed, seeds, hired, invs, obs)
            return orders + base_orders

        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if day == 6:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    if self.mode == "force1_d6":
                        new_orders.append(["BUY_ANIMAL", "COW", min(1, int(o[2]))])
                    elif self.mode == "force2_d6":
                        new_orders.append(["BUY_ANIMAL", "COW", 2])
                    elif self.mode == "day7":
                        # Delay cow buy from day 6 to day 7
                        pass
                else:
                    new_orders.append(o)
            return new_orders
        elif day == 7 and self.mode == "day7" and hour == 0:
            cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
            cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
            cows_needed = max(0, 8 - cows_tot)
            if cows_needed > 0 and money >= 650:
                can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                if can_buy_c > 0:
                    orders.append(["BUY_ANIMAL", "COW", can_buy_c])
            return orders
        return orders

def evaluate_seed_phases(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_agent_track(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        # Financial tracking by category
        flows = {
            "rev_wheat": 0, "rev_wool": 0, "rev_milk": 0, "rev_straw": 0, "rev_melon": 0, "rev_fert": 0,
            "exp_cow": 0, "exp_sheep": 0, "exp_seed_wheat": 0, "exp_seed_straw": 0, "exp_seed_melon": 0,
            "exp_feed": 0, "exp_hire": 0, "exp_land": 0
        }
        sold = {"WHEAT": 0, "WOOL": 0, "MILK": 0, "STRAWBERRY": 0, "MELON": 0, "FERTILIZER": 0}
        sheep_shed_days = 0
        cow_shed_days = 0
        wool_cycles = 0
        milk_cycles = 0
        
        for s_idx, st in enumerate(steps):
            day = s_idx // 24
            hr = s_idx % 24
            p0 = st[0]
            obs = p0.get("observation") or {}
            act = p0.get("action") or {}
            farm = (obs.get("farms") or [{}, {}])[0]
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            
            if s_idx % 24 == 23:
                sheep_shed_days += int(shed.get("SHEEP", 0) or 0)
                cow_shed_days += int(shed.get("COW", 0) or 0)

            # Check harvest of wool/milk
            tiles = farm.get("tiles") or []
            for r in tiles:
                for t in r:
                    if isinstance(t, dict) and "animal" in t:
                        if t.get("animal") == "SHEEP" and t.get("cared_today") and t.get("fed_today"):
                            # On production day
                            pass

            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3:
                    cmd, item, qty = o[0], o[1], int(o[2])
                    if cmd == "SELL":
                        if item in sold: sold[item] += qty
                        # We track revenue approx or exact
                    elif cmd == "BUY_ANIMAL":
                        if item == "COW": flows["exp_cow"] += qty * 400
                        elif item == "SHEEP": flows["exp_sheep"] += qty * 500
                    elif cmd == "BUY_SEED":
                        if item == "WHEAT": flows["exp_seed_wheat"] += qty * 10
                        elif item == "STRAWBERRY": flows["exp_seed_straw"] += qty * 100
                        elif item == "MELON": flows["exp_seed_melon"] += qty * 80
                    elif cmd == "BUY_PRODUCT" and item == "WHEAT":
                        flows["exp_feed"] += qty * 30 # approx base market price

        rew = steps[-1][0]["reward"]
        return {
            "reward": rew,
            "sold": sold,
            "flows": flows,
            "sheep_shed_days": sheep_shed_days,
            "cow_shed_days": cow_shed_days
        }

    m1 = run_agent_track(m1_module.ClosedLoopEconomicV1())
    q50 = run_agent_track(ParameterizedQuotaAgent(50))
    v2 = run_agent_track(v2_agent)
    
    # Phase 9 variants
    m1_force1 = run_agent_track(M1CowTimingVariant("force1_d6"))
    m1_force2 = run_agent_track(M1CowTimingVariant("force2_d6"))
    m1_day5 = run_agent_track(M1CowTimingVariant("day5"))
    m1_day7 = run_agent_track(M1CowTimingVariant("day7"))

    return {
        "seed": seed,
        "m1": m1,
        "q50": q50,
        "v2": v2,
        "m1_force1": m1_force1,
        "m1_force2": m1_force2,
        "m1_day5": m1_day5,
        "m1_day7": m1_day7
    }

def main():
    seeds = list(range(1000, 1030)) # 30 seeds for deep multi-arm study
    print(f"Running multi-phase audit on {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(evaluate_seed_phases, seeds))

    with open("scratch/phases_8_9_12_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Finished evaluating phases 8, 9, 12.")

if __name__ == "__main__":
    main()
