import sys
import os
import json
import time
from collections import defaultdict
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

# Define Candidate B Variants

# B1: Standard B_only (suppress weeds when ANY ripe strawberry exists)
class B1_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if len(ripe_straws) >= 1:
            res["weeds"] = []
        return res

# B2: Suppress weeds only when >= 2 ripe strawberries exist
class B2_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if len(ripe_straws) >= 2:
            res["weeds"] = []
        return res

# B3: Suppress weeds only when >= 3 ripe strawberries exist
class B3_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if len(ripe_straws) >= 3:
            res["weeds"] = []
        return res

# B4: Suppress weeds when ripe strawberry exists AND field workload is high (unwatered + ripe >= 10)
class B4_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        high_workload = (len(res["unwatered"]) + len(res["ripe_crops"])) >= 10
        if len(ripe_straws) >= 1 and high_workload:
            res["weeds"] = []
        return res

# B5: Suppress weeds when ripe strawberry exists AND no animals are hungry (res["hungry"] == 0)
class B5_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        no_hungry = len(res["hungry"]) == 0
        if len(ripe_straws) >= 1 and no_hungry:
            res["weeds"] = []
        return res

# B6: Suppress weeds when ripe strawberry exists AND total strawberry bushes >= 15
class B6_Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straws = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        total_straws = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
        if len(ripe_straws) >= 1 and total_straws >= 15:
            res["weeds"] = []
        return res

def run_single_simulation(args):
    pol_name, seed = args
    if pol_name == "Raw_Q50": agent = BaseQ50Agent(50)
    elif pol_name == "B1":    agent = B1_Agent(50)
    elif pol_name == "B2":    agent = B2_Agent(50)
    elif pol_name == "B3":    agent = B3_Agent(50)
    elif pol_name == "B4":    agent = B4_Agent(50)
    elif pol_name == "B5":    agent = B5_Agent(50)
    elif pol_name == "B6":    agent = B6_Agent(50)
    elif pol_name == "L_Min": agent = L_MinimalAgent(50)
    else: raise ValueError(f"Unknown {pol_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])

    env_rew = float(steps[-1][0]["reward"])

    # Detailed action & telemetry extraction
    act_counts = defaultdict(int)
    total_moves = 0
    missed_water = 0
    straw_deaths = 0
    mature_straw_hours = 0
    weed_count_sum = 0
    worker_congestion_sum = 0

    prev_straw_tiles = set()

    for s_idx, st in enumerate(steps):
        act = st[0].get("action") or {}
        obs = st[0]["observation"]
        farm = obs["farms"][0]
        tiles = farm["tiles"]

        f_act = act.get("farmer")
        h_acts = act.get("hands") or []
        for a in [f_act] + h_acts:
            if a and isinstance(a, list) and len(a) > 0:
                op = a[0]
                act_counts[op] += 1
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    total_moves += 1

        curr_straw_tiles = set()
        curr_weeds = 0
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if isinstance(t, dict):
                    if t.get("crop") == "STRAWBERRY":
                        curr_straw_tiles.add((c, r))
                        if t.get("yield_units", 0) > 0:
                            mature_straw_hours += 1
                        if t.get("consecutive_unwatered", 0) > 0:
                            missed_water += 1
                    elif t.get("kind") == "WEED":
                        curr_weeds += 1
        
        # Check deaths
        dead = prev_straw_tiles - curr_straw_tiles
        for dpos in dead:
            t = tiles[dpos[1]][dpos[0]]
            if isinstance(t, dict) and t.get("kind") == "WEED":
                straw_deaths += 1
        prev_straw_tiles = curr_straw_tiles

        weed_count_sum += curr_weeds
        worker_congestion_sum += len(h_acts)

    # Market quantities
    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return {
        "policy": pol_name,
        "seed": seed,
        "reward": env_rew,
        "moves": total_moves,
        "dig": act_counts["DIG"],
        "water": act_counts["WATER"],
        "harvest": act_counts["HARVEST"],
        "care": act_counts["CARE"],
        "feed": act_counts["FEED"],
        "plant": act_counts["PLANT"],
        "missed_water": missed_water,
        "straw_deaths": straw_deaths,
        "mature_straw_hours": mature_straw_hours,
        "avg_weeds": weed_count_sum / len(steps),
        "sold_qty": dict(sold_qty)
    }

def main():
    # Pristine 100-seed cohort with ZERO prior matches repository-wide
    seeds = list(range(841000, 841100))
    policies = ["Raw_Q50", "B1", "B2", "B3", "B4", "B5", "B6", "L_Min"]

    print("=" * 100)
    print(f"RUNNING EXPERIMENTAL DISCOVERY ON PRISTINE SEEDS 841000-841099 (N={len(seeds)})")
    print(f"Policies ({len(policies)}): {policies}")
    print("=" * 100, flush=True)

    jobs = [(p, s) for p in policies for s in seeds]
    results = defaultdict(dict)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=11) as executor:
        for i, res in enumerate(executor.map(run_single_simulation, jobs, chunksize=5)):
            results[res["policy"]][res["seed"]] = res
            if (i + 1) % 100 == 0 or (i + 1) == len(jobs):
                print(f"  Progress: {i + 1}/{len(jobs)} runs completed ({time.time() - t0:.1f}s)", flush=True)

    with open("scratch/clean_discovery_841000_raw_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved complete simulation results to scratch/clean_discovery_841000_raw_results.json")

if __name__ == "__main__":
    main()
