import json
import os
import sys
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_fert_gated import ClosedLoopEconomicV1 as BaseAgent

SEEDS_50 = list(range(1000, 1050))
QUOTAS = [40, 45, 50, 55, 60, 65, 70]

class ParameterizedQuotaAgent(BaseAgent):
    def __init__(self, quota):
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
        rem = max(0, self.quota - self.total_wheat_planted)
        if len(res["plant_w"]) > rem:
            res["plant_w"] = res["plant_w"][:rem]
        return res

def run_quota_match(args):
    quota, seed = args
    agent_inst = ParameterizedQuotaAgent(quota)
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent_inst, "starter"])
    p = 0
    total_steps = len(steps)

    actions_count = {
        "PLANT": 0, "HARVEST": 0, "WATER": 0, "FERTILIZE": 0, "FEED": 0,
        "CARE": 0, "COLLECT_FERTILIZER": 0, "DROP": 0, "PICKUP": 0,
        "MOVE": 0, "PASS": 0, "OTHER": 0
    }
    straw_harvest_actions = 0
    animal_care_actions = 0
    animal_feed_actions = 0

    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    exp_seeds = 0.0
    exp_feed = 0.0

    wheat_planted_plots = 0
    wheat_harvested_units = 0
    straw_planted_events = 0
    straw_harvested_units = 0
    straw_fertilized_events = 0

    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx - 1][p]["observation"]
        curr_obs = steps[s_idx][p]["observation"]
        prev_farm = prev_obs["farms"][p]
        curr_farm = curr_obs["farms"][p]
        prev_priv = prev_obs.get("private") or {}
        act = steps[s_idx][p].get("action") or {}
        prev_prices = (prev_obs.get("market") or {}).get("prices") or {}

        for order in act.get("market") or []:
            if not isinstance(order, list) or len(order) < 2:
                continue
            cmd = order[0]
            item = order[1]
            qty = int(order[2]) if len(order) > 2 else 1
            if cmd == "SELL" and item in rev_by_item:
                p_val = float(prev_prices.get(item, 0.0))
                rev_by_item[item] += qty * p_val
                qty_sold[item] += qty
            elif cmd == "BUY_SEED":
                cost = 10 if item == "WHEAT" else (100 if item == "STRAWBERRY" else (80 if item == "MELON" else 50))
                exp_seeds += qty * cost
            elif cmd == "BUY_PRODUCT" and item == "WHEAT":
                exp_feed += qty * 30

        all_wacts = [act.get("farmer")] + (act.get("hands") or [])
        positions = [prev_farm.get("farmer")] + (prev_farm.get("hands") or [])
        for w_idx, wact in enumerate(all_wacts):
            if not wact:
                actions_count["PASS"] += 1
                continue
            op = wact[0] if isinstance(wact, list) and len(wact) > 0 else (wact if isinstance(wact, str) else "PASS")
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                actions_count["MOVE"] += 1
            elif op in actions_count:
                actions_count[op] += 1
            else:
                actions_count["OTHER"] += 1

            wpos = positions[w_idx] if w_idx < len(positions) else None
            if op == "FEED":
                animal_feed_actions += 1
            elif op == "CARE":
                animal_care_actions += 1
            elif op == "HARVEST":
                if wpos:
                    wx, wy = wpos
                    pt = prev_farm["tiles"][wy][wx] if 0 <= wy < len(prev_farm["tiles"]) and 0 <= wx < len(prev_farm["tiles"][0]) else None
                    if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                        straw_harvest_actions += 1
            elif op == "PLANT":
                plant_crop = wact[1] if len(wact) > 1 else None
                if plant_crop == "STRAWBERRY":
                    straw_planted_events += 1

        p_tiles = prev_farm.get("tiles") or []
        c_tiles = curr_farm.get("tiles") or []
        workers = [prev_farm.get("farmer")] + (prev_farm.get("hands") or [])
        day = s_idx // 24

        for r in range(len(p_tiles)):
            for c in range(len(p_tiles[r])):
                pt = p_tiles[r][c]
                ct = c_tiles[r][c]
                p_crop = pt.get("crop") if isinstance(pt, dict) else None
                c_crop = ct.get("crop") if isinstance(ct, dict) else None

                if p_crop != "WHEAT" and c_crop == "WHEAT":
                    wheat_planted_plots += 1

                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    p_fert = pt.get("fertilized_until_day", -1)
                    c_fert = ct.get("fertilized_until_day", -1) if isinstance(ct, dict) else -1
                    if c_fert > p_fert and c_fert >= day:
                        straw_fertilized_events += 1
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "STRAWBERRY" else 0
                    if py > cy and [c, r] in workers:
                        straw_harvested_units += (py - cy)

                if isinstance(pt, dict) and pt.get("crop") == "WHEAT":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "WHEAT" else 0
                    if py > cy and [c, r] in workers:
                        wheat_harvested_units += (py - cy)

    last_farm = steps[-1][p]["observation"]["farms"][p]
    terminal_reward = float(last_farm.get("money") or 0.0)

    return {
        "quota": quota,
        "seed": seed,
        "terminal_reward": terminal_reward,
        "wheat_planted_plots": wheat_planted_plots,
        "wheat_harvested_units": wheat_harvested_units,
        "wheat_sold": qty_sold["WHEAT"],
        "wheat_rev": rev_by_item["WHEAT"],
        "straw_sold": qty_sold["STRAWBERRY"],
        "straw_rev": rev_by_item["STRAWBERRY"],
        "melon_sold": qty_sold["MELON"],
        "melon_rev": rev_by_item["MELON"],
        "milk_sold": qty_sold["MILK"],
        "milk_rev": rev_by_item["MILK"],
        "wool_sold": qty_sold["WOOL"],
        "wool_rev": rev_by_item["WOOL"],
        "fert_sold": qty_sold["FERTILIZER"],
        "fert_rev": rev_by_item["FERTILIZER"],
        "exp_seeds": exp_seeds,
        "exp_feed": exp_feed,
        "moves": actions_count["MOVE"],
        "passes": actions_count["PASS"],
        "straw_planted_events": straw_planted_events,
        "straw_harvested_units": straw_harvested_units,
        "straw_fertilized_events": straw_fertilized_events,
        "straw_harvest_actions": straw_harvest_actions,
        "animal_care_actions": animal_care_actions,
        "animal_feed_actions": animal_feed_actions,
        "actions_count": actions_count
    }

def main():
    print(f"Executing Quota Sweep [40, 45, 50, 55, 60, 65, 70] across 50 matched seeds (1000-1049)...")
    tasks = []
    for q in QUOTAS:
        for s in SEEDS_50:
            tasks.append((q, s))

    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(run_quota_match, tasks):
            results.append(res)
            if len(results) % 50 == 0:
                print(f"Processed {len(results)}/{len(tasks)} quota matches ({time.time()-t0:.1f}s)...", flush=True)

    out_path = "scratch/wheat_quota_sweep_50seeds_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path} in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
