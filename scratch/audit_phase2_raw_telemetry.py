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
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent

def trace_seed_telemetry(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_agent(agent, agent_name):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        hourly_cash = {}
        market_orders = []
        buy_animal_orders = []
        wheat_sales = []
        pickups = []
        placements = []
        daily_sheep_on_field = {}
        daily_cows_on_field = {}
        daily_wool_harvested = defaultdict(int)
        daily_milk_harvested = defaultdict(int)
        sheep_deploy_day = {} # sheep index -> day deployed
        sheep_placed_tiles = []
        cow_placed_tiles = []
        
        sold = defaultdict(int)
        spent = defaultdict(int)
        
        for s_idx in range(len(steps)):
            day = s_idx // 24
            hr = s_idx % 24
            p0 = steps[s_idx][0]
            obs = p0.get("observation") or {}
            act = p0.get("action") or {}
            farm = (obs.get("farms") or [{}, {}])[0]
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            tiles = farm.get("tiles") or []
            money = farm.get("money", 0)

            # Record hourly cash for Days 3 to 10
            if 3 <= day <= 10:
                hourly_cash[f"D{day}H{hr}"] = money

            # Daily occupancy snapshots at H23
            if hr == 23:
                n_cows = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
                n_sheep = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
                daily_cows_on_field[day] = n_cows
                daily_sheep_on_field[day] = n_sheep

            # Market orders
            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3:
                    cmd, item, qty = o[0], o[1], int(o[2])
                    market_orders.append({"step": s_idx, "day": day, "hr": hr, "cmd": cmd, "item": item, "qty": qty})
                    if cmd == "BUY_ANIMAL":
                        buy_animal_orders.append({"step": s_idx, "day": day, "hr": hr, "animal": item, "qty": qty, "money": money})
                    elif cmd == "SELL":
                        sold[item] += qty
                        if item == "WHEAT":
                            wheat_sales.append({"step": s_idx, "day": day, "hr": hr, "qty": qty})
                    elif cmd == "BUY_SEED":
                        cost_per = {"WHEAT": 10, "STRAWBERRY": 100, "MELON": 80, "CARROT": 20, "TOMATO": 50}.get(item, 10)
                        spent[f"SEED_{item}"] += qty * cost_per
                    elif cmd == "BUY_PRODUCT":
                        spent[f"PROD_{item}"] += qty * 30

            # Worker actions
            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            for w_idx, wa in enumerate(w_acts):
                if isinstance(wa, list) and len(wa) >= 2:
                    op = wa[0]
                    it = wa[1]
                    pos = farm.get("farmer", [0, 0]) if w_idx == 0 else (farm.get("hands", [])[w_idx-1] if w_idx-1 < len(farm.get("hands", [])) else [0, 0])
                    if op == "PICKUP":
                        pickups.append({"step": s_idx, "day": day, "hr": hr, "worker": w_idx, "item": it, "qty": int(wa[2]) if len(wa) > 2 else 1})
                    elif op == "PLACE":
                        placements.append({"step": s_idx, "day": day, "hr": hr, "worker": w_idx, "item": it, "pos": tuple(pos)})
                        if it == "SHEEP":
                            sheep_placed_tiles.append({"day": day, "pos": tuple(pos)})
                        elif it == "COW":
                            cow_placed_tiles.append({"day": day, "pos": tuple(pos)})
                    elif op == "HARVEST":
                        x, y = pos
                        t = tiles[y][x] if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]) else None
                        if isinstance(t, dict) and "animal" in t:
                            if t["animal"] == "SHEEP":
                                daily_wool_harvested[day] += int(t.get("yield_units", 0) or 0)
                            elif t["animal"] == "COW":
                                daily_milk_harvested[day] += int(t.get("yield_units", 0) or 0)

        rew = steps[-1][0]["reward"]
        
        # Deployment day of sheep 1 to 6
        sheep_by_day = [p["day"] for p in sheep_placed_tiles]
        
        return {
            "name": agent_name,
            "reward": rew,
            "sold": dict(sold),
            "spent": dict(spent),
            "hourly_cash": hourly_cash,
            "buy_animal_orders": buy_animal_orders,
            "wheat_sales_count": len(wheat_sales),
            "total_wheat_sold": sold.get("WHEAT", 0),
            "total_wool_sold": sold.get("WOOL", 0),
            "total_straw_sold": sold.get("STRAWBERRY", 0),
            "total_milk_sold": sold.get("MILK", 0),
            "daily_cows_on_field": daily_cows_on_field,
            "daily_sheep_on_field": daily_sheep_on_field,
            "daily_wool_harvested": dict(daily_wool_harvested),
            "sheep_placed_tiles": sheep_placed_tiles,
            "cow_placed_tiles": cow_placed_tiles,
            "cows_on_sheep_slots": [p for p in cow_placed_tiles if p["pos"] in {(4, 2), (2, 4), (5, 4), (6, 4), (5, 3), (6, 3)}]
        }

    m1 = run_agent(m1_module.ClosedLoopEconomicV1(), "M1")
    q50 = run_agent(ParameterizedQuotaAgent(50), "Q50")
    mech_a = run_agent(MechanismAAgent(50), "MechA")

    return {
        "seed": seed,
        "m1": m1,
        "q50": q50,
        "mech_a": mech_a
    }

def main():
    # Run on Seeds 1000-1049 (50 seeds) and 1050-1149 (100 seeds)
    all_seeds = list(range(1000, 1050)) + list(range(1050, 1150))
    print(f"Rebuilding economic causal chain across {len(all_seeds)} seeds (1000-1149)...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(trace_seed_telemetry, all_seeds))

    with open("scratch/raw_telemetry_150seeds.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Finished raw telemetry extraction. Saved to scratch/raw_telemetry_150seeds.json.")

if __name__ == "__main__":
    main()
