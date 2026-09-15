import sys
import os
import copy
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1, CROPS_DEF

class CausalSuccessionAgent(ClosedLoopEconomicV1):
    def __init__(self, mode="BASELINE"):
        super().__init__()
        self.mode = mode

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        if self.mode == "BASELINE":
            return orders

        # Midday / Hour 1 succession seed procurement (Days 4 to 22) when market queue has room!
        # At hour 0, super() orders can reach 10, but at hour 1, queues are empty!
        if (hour == 1 or hour == 12) and 4 <= day <= 22 and len(orders) < 10:
            rem_days = 30 - day

            if self.mode == "TEST1_REPLANT_ONLY":
                # Simplest replanting: buy wheat seeds to immediately reseed vacated tiles
                wheat_s = int(seeds.get("WHEAT", 0) or 0)
                if rem_days >= 4 and wheat_s < 8 and money >= 150:
                    buy_cnt = min(8 - wheat_s, min(4, int((money - 100) // 10)))
                    if buy_cnt > 0 and len(orders) < 10:
                        orders.append(["BUY_SEED", "WHEAT", buy_cnt])

            elif self.mode == "TEST2_CROP_CHOICE":
                # Crop-choice based on remaining season time
                # If rem_days >= 13: Melon ($80 seed, $250 yield)
                # Else if rem_days >= 4: Wheat ($10 seed, $25 yield)
                melon_s = int(seeds.get("MELON", 0) or 0)
                wheat_s = int(seeds.get("WHEAT", 0) or 0)
                if rem_days >= 13 and melon_s < 4 and money >= 250 and len(orders) < 10:
                    buy_m = min(4 - melon_s, min(3, int((money - 150) // 80)))
                    if buy_m > 0:
                        orders.append(["BUY_SEED", "MELON", buy_m])
                elif 4 <= rem_days < 13 and wheat_s < 8 and money >= 150 and len(orders) < 10:
                    buy_w = min(8 - wheat_s, min(4, int((money - 100) // 10)))
                    if buy_w > 0:
                        orders.append(["BUY_SEED", "WHEAT", buy_w])

            elif self.mode == "TEST3_CAPITAL_CONSTRAINED":
                # Only buy succession seeds if money >= $400 (protect livestock & hiring buffer)
                if money >= 400:
                    if rem_days >= 13 and len(orders) < 10:
                        melon_s = int(seeds.get("MELON", 0) or 0)
                        buy_m = min(3, int((money - 300) // 80))
                        if buy_m > 0:
                            orders.append(["BUY_SEED", "MELON", buy_m])
                    elif rem_days >= 4 and len(orders) < 10:
                        wheat_s = int(seeds.get("WHEAT", 0) or 0)
                        buy_w = min(4, int((money - 200) // 10))
                        if buy_w > 0:
                            orders.append(["BUY_SEED", "WHEAT", buy_w])

            elif self.mode == "TEST4_WORKER_FEASIBLE":
                # Only reseed if worker count >= 8 so field maintenance is not starved
                n_workers = len(invs)
                if n_workers >= 8 and money >= 250:
                    if rem_days >= 13 and len(orders) < 10:
                        melon_s = int(seeds.get("MELON", 0) or 0)
                        buy_m = min(3, int((money - 150) // 80))
                        if buy_m > 0:
                            orders.append(["BUY_SEED", "MELON", buy_m])
                    elif rem_days >= 4 and len(orders) < 10:
                        wheat_s = int(seeds.get("WHEAT", 0) or 0)
                        buy_w = min(4, int((money - 150) // 10))
                        if buy_w > 0:
                            orders.append(["BUY_SEED", "WHEAT", buy_w])

            elif self.mode == "TEST5_INTEGRATED":
                # Integrated: rem_days check (>=13 for melon, >=4 for wheat) + capital buffer >= $350 + worker count >= 8
                n_workers = len(invs)
                if n_workers >= 8 and money >= 350:
                    if rem_days >= 13 and len(orders) < 10:
                        melon_s = int(seeds.get("MELON", 0) or 0)
                        buy_m = min(3, int((money - 250) // 80))
                        if buy_m > 0:
                            orders.append(["BUY_SEED", "MELON", buy_m])
                    elif rem_days >= 4 and len(orders) < 10:
                        wheat_s = int(seeds.get("WHEAT", 0) or 0)
                        buy_w = min(4, int((money - 150) // 10))
                        if buy_w > 0:
                            orders.append(["BUY_SEED", "WHEAT", buy_w])

        return orders[:10]

def run_succession_experiment_match(args):
    mode, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    agent_inst = CausalSuccessionAgent(mode=mode)
    env.run([agent_inst, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvest_ops = 0
    total_plant_ops = 0
    total_moves = 0
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a: continue
            op = a[0]
            if op == "HARVEST":
                total_harvest_ops += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    k = t.get("kind")
                    yu = int(t.get("yield_units", 0) or 0)
                    if k == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif k == "PASTURE": harvest_counts[t.get("animal")] += yu
            elif op == "PLANT":
                total_plant_ops += 1
            elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    
    return {
        "mode": mode,
        "seed": seed,
        "reward": reward,
        "harvest_ops": total_harvest_ops,
        "plant_ops": total_plant_ops,
        "moves": total_moves,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "crop_units_total": harvest_counts.get("STRAWBERRY", 0) + harvest_counts.get("WHEAT", 0) + harvest_counts.get("MELON", 0)
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1010))
    modes = [
        "BASELINE",
        "TEST1_REPLANT_ONLY",
        "TEST2_CROP_CHOICE",
        "TEST3_CAPITAL_CONSTRAINED",
        "TEST4_WORKER_FEASIBLE",
        "TEST5_INTEGRATED"
    ]
    tasks = []
    for m in modes:
        for s in seeds:
            tasks.append((m, s))
            
    print(f"Running Causal Succession Hierarchy Study (6 modes x {len(seeds)} seeds = {len(tasks)} matches)...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_succession_experiment_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["mode"]].append(res)
            
    with open("scratch/audit_causal_succession_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)
        
    print("\n" + "="*110)
    print(f"{'MODE':<26} | {'Reward ($)':<16} | {'Harvests':<9} | {'Plants':<7} | {'Crop Units':<10} | {'Straw':<7} | {'Melon':<7} | {'Wheat':<7}")
    print("-" * 110)
    
    for m in modes:
        lst = results[m]
        lst.sort(key=lambda x: x["seed"])
        rews = [x["reward"] for x in lst]
        harvs = [x["harvest_ops"] for x in lst]
        plants = [x["plant_ops"] for x in lst]
        c_units = [x["crop_units_total"] for x in lst]
        straw = [x["straw"] for x in lst]
        melon = [x["melon"] for x in lst]
        wheat = [x["wheat"] for x in lst]
        
        m_rew = float(np.mean(rews))
        std_rew = float(np.std(rews))
        ci95 = 1.96 * std_rew / np.sqrt(len(rews))
        
        print(f"{m:<26} | ${m_rew:10.2f} ± ${ci95:5.0f} | {np.mean(harvs):9.1f} | {np.mean(plants):7.1f} | {np.mean(c_units):10.1f} | {np.mean(straw):7.1f} | {np.mean(melon):7.1f} | {np.mean(wheat):7.1f}")
