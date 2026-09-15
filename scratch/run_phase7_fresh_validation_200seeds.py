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
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent

def run_single_seed(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_agent(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        sold = defaultdict(int)
        spent = defaultdict(int)
        hourly_cash = {}
        day6_cows_bought = 0
        sheep_shed_days = 0
        cows_on_sheep_slots = 0
        
        for s_idx, st in enumerate(steps):
            day = s_idx // 24
            hr = s_idx % 24
            p0 = st[0]
            obs = p0.get("observation") or {}
            act = p0.get("action") or {}
            farm = (obs.get("farms") or [{}, {}])[0]
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            money = farm.get("money", 0)

            if day == 6 and hr == 0:
                hourly_cash["D6H0"] = money

            if s_idx % 24 == 23:
                sheep_shed_days += int(shed.get("SHEEP", 0) or 0)

            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3:
                    cmd, item, qty = o[0], o[1], int(o[2])
                    if cmd == "SELL":
                        sold[item] += qty
                    elif cmd == "BUY_ANIMAL":
                        if item == "COW":
                            spent["BUY_COW"] += qty * 400
                            if day == 6:
                                day6_cows_bought += qty
                        elif item == "SHEEP":
                            spent["BUY_SHEEP"] += qty * 500
                    elif cmd == "BUY_SEED":
                        cost_per = {"WHEAT": 10, "STRAWBERRY": 100, "MELON": 80}.get(item, 10)
                        spent[f"SEED_{item}"] += qty * cost_per
                    elif cmd == "BUY_PRODUCT":
                        spent[f"FEED_{item}"] += qty * 30

        tiles = (steps[-1][0]["observation"].get("farms") or [{}])[0].get("tiles") or []
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("animal") == "COW":
                    if m1_module.PASTURE_SPECIES.get((x, y)) == "SHEEP":
                        cows_on_sheep_slots += 1

        return {
            "reward": steps[-1][0]["reward"],
            "sold": dict(sold),
            "spent": dict(spent),
            "d6_cash": hourly_cash.get("D6H0", 0),
            "day6_cows_bought": day6_cows_bought,
            "sheep_shed_days": sheep_shed_days,
            "cows_on_sheep_slots": cows_on_sheep_slots
        }

    m1_data = run_agent(m1_module.ClosedLoopEconomicV1())
    mecha_data = run_agent(MechanismAAgent(50))

    return {
        "seed": seed,
        "m1": m1_data,
        "mech_a": mecha_data
    }

def main():
    seeds = list(range(1250, 1450)) # 200 completely fresh seeds
    print(f"Running Phase 7 Fresh 200-Seed Validation (Seeds 1250-1449)...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_single_seed, seeds))

    with open("scratch/phase7_validation_200seeds_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Phase 7 200-seed validation complete. Saved to scratch/phase7_validation_200seeds_results.json.")

if __name__ == "__main__":
    main()
