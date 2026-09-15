import sys
import os
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# 1. Counterfactual A: Strict Sheep Slot Preservation
# A cow is never allowed to be placed on a SHEEP designated slot (PASTURE_SPECIES[pos] == "SHEEP").
# A cow is only targeted to cow slots.
class SheepSlotPreservationAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # We override Step 1 placement and Step 3 placement targets to strictly forbid cows on sheep slots
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = m1_module._nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-First Execution on Current Tile
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < m1_module.BOARD and 0 <= x < m1_module.BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in m1_module.PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            # Shed drop
            if pos in m1_module.SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    can_fert = False
                    if crop == "STRAWBERRY":
                        p_day = int(t.get("planted_day", 0) or 0)
                        can_fert = (p_day + 7 <= day <= min(29, p_day + 15))
                    elif crop != "WHEAT":
                        can_fert = True

                    if can_fert and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles:
                        actions[i] = ["WATER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["FEED"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if not t.get("cared_today") and pos not in claimed_action_tiles:
                            actions[i] = ["CARE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if t.get("fertilizer_available") and pos not in claimed_action_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    else:
                        desired_sp = m1_module.PASTURE_SPECIES.get(pos, "COW")
                        # STRICT SLOT PRESERVATION: Only place matching species!
                        if desired_sp == "SHEEP" and sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif desired_sp == "COW" and cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "WEED" and pos not in claimed_action_tiles:
                    actions[i] = ["DIG"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_action_tiles:
                    actions[i] = ["BUILD_PASTURE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

        # Step 2: Validate commitments
        unassigned_workers = []
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue
            produce_load = sum(int(inv.get(it, 0) or 0) for it in m1_module.PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            valid = False
            
            if i in self._worker_targets:
                active_t, task_type, sc = self._worker_targets[i]
                if sc < 15 and active_t not in claimed_action_tiles:
                    ax, ay = active_t
                    at = tiles[ay][ax] if 0 <= ay < m1_module.BOARD and 0 <= ax < m1_module.BOARD else None
                    if task_type == "WATER" and isinstance(at, dict) and not at.get("watered_today"): valid = True
                    elif task_type == "HARVEST" and isinstance(at, dict) and int(at.get("yield_units", 0) or 0) > 0: valid = True
                    elif task_type == "FEED" and w_inv > 0 and isinstance(at, dict) and not at.get("fed_today"): valid = True
                    elif task_type == "DROP" and produce_load > 0: valid = True
                    
                    if valid:
                        self._worker_targets[i] = (active_t, task_type, sc + 1)
                        claimed_action_tiles.add(active_t)
                        actions[i] = [m1_module._bfs_step(pos, active_t, tiles)]
                    else:
                        self._worker_targets.pop(i, None)
                else:
                    self._worker_targets.pop(i, None)
            if not valid:
                unassigned_workers.append(i)

        if not unassigned_workers:
            return actions

        # Step 3: Animal handling with STRICT SPECIES SLOT TARGETING
        has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
        still_unassigned = []
        for w in unassigned_workers:
            pos = all_workers[w]
            inv = all_invs[w]
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            
            if (cow_inv + sheep_inv) > 0:
                car_sp = "COW" if cow_inv > 0 else "SHEEP"
                # STRICT: only match slots designated for this species!
                matching_slots = [p for p in target_pasture_slots if m1_module.PASTURE_SPECIES.get(p) == car_sp and p not in claimed_action_tiles]
                cands = [p for p in matching_slots if p in scan_res["empty_p"]] or [p for p in matching_slots if p in scan_res["unbuilt_p"]]
                if cands:
                    t = min(cands, key=lambda p: m1_module._dist(pos, p))
                    claimed_action_tiles.add(t)
                    self._worker_targets[w] = (t, "PLACE", 1)
                    actions[w] = [m1_module._bfs_step(pos, t, tiles)]
                    continue
            elif has_animals_in_shed and (cow_inv + sheep_inv) == 0 and (w in (0, 1) or hour <= 3):
                if pos in m1_module.SHED_ACCESS:
                    if int(shed.get("COW", 0) or 0) > 0: actions[w] = ["PICKUP", "COW", 1]; continue
                    elif int(shed.get("SHEEP", 0) or 0) > 0: actions[w] = ["PICKUP", "SHEEP", 1]; continue
                else:
                    claimed_action_tiles.add(ns)
                    self._worker_targets[w] = (ns, "PICKUP", 1)
                    actions[w] = [m1_module._bfs_step(pos, ns, tiles)]
                    continue

            if scan_res["hungry"]:
                if w_inv > 0:
                    cands = [h for h in scan_res["hungry"] if h not in claimed_action_tiles]
                    if cands:
                        t = min(cands, key=lambda p: m1_module._dist(pos, p))
                        claimed_action_tiles.add(t)
                        self._worker_targets[w] = (t, "FEED", 1)
                        actions[w] = [m1_module._bfs_step(pos, t, tiles)]
                        continue
                elif int(shed.get("WHEAT", 0) or 0) > 0 and (w in (0, 1, 2, 3) or hour <= 6):
                    if pos in m1_module.SHED_ACCESS:
                        batch_pickup = min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))
                        actions[w] = ["PICKUP", "WHEAT", batch_pickup]
                        continue
                    else:
                        claimed_action_tiles.add(ns)
                        self._worker_targets[w] = (ns, "PICKUP", 1)
                        actions[w] = [m1_module._bfs_step(pos, ns, tiles)]
                        continue
            
            still_unassigned.append(w)

        if not still_unassigned:
            return actions

        # Step 4: Fall through to standard priority pools
        priority_pools = [
            ("URGENT_WATER", scan_res["urgent_unwatered"]),
            ("RIPE_ANIMAL", scan_res["ripe_a"]),
            ("FERT", scan_res["fert"]),
            ("HARVEST_CROPS", scan_res["ripe_crops"]),
            ("WATER_CROPS", scan_res["unwatered"]),
            ("PLANT_STRAW", scan_res["plant_s"] if int(seeds.get("STRAWBERRY", 0) or 0) > 0 else []),
            ("PLANT_MELON", scan_res["plant_m"] if int(seeds.get("MELON", 0) or 0) > 0 else []),
            ("PLANT_WHEAT", scan_res["plant_w"] if int(seeds.get("WHEAT", 0) or 0) > 0 else []),
            ("UNBUILT_P", scan_res["unbuilt_p"]),
            ("WEEDS", scan_res["weeds"]),
        ]

        assigned_workers = set()
        for pool_name, pool_cands in priority_pools:
            avail_cands = [c for c in pool_cands if c not in claimed_action_tiles]
            avail_workers = [w for w in still_unassigned if w not in assigned_workers]
            if not avail_cands or not avail_workers:
                continue

            cost_matrix = []
            for w in avail_workers:
                w_pos = all_workers[w]
                pref_q = self._worker_preferred_quad(w)
                row = []
                for c in avail_cands:
                    d = m1_module._dist(w_pos, c)
                    c_q = m1_module._quad(c[0], c[1])
                    zone_pen = 0.0 if c_q == pref_q else 2.0
                    cx, cy = c
                    cb = 0.0
                    for ox, oy in avail_cands:
                        if (ox, oy) == c: continue
                        cd = abs(cx - ox) + abs(cy - oy)
                        if cd == 1: cb += 2.5
                        elif cd == 2: cb += 1.0
                    local_bonus = 3.0 if d <= 2 else 0.0
                    cost = d + zone_pen - 0.4 * cb - local_bonus
                    row.append(cost)
                cost_matrix.append(row)

            matching = m1_module.min_cost_bipartite_matching(cost_matrix)
            for w_idx_sub, c_idx_sub in matching:
                w = avail_workers[w_idx_sub]
                chosen_cand = avail_cands[c_idx_sub]
                claimed_action_tiles.add(chosen_cand)
                assigned_workers.add(w)
                self._worker_targets[w] = (chosen_cand, pool_name, 1)
                actions[w] = [m1_module._bfs_step(all_workers[w], chosen_cand, tiles)]

        # Step 5: Fallback
        for w in still_unassigned:
            if w not in assigned_workers:
                pos = all_workers[w]
                inv = all_invs[w]
                produce_load = sum(int(inv.get(it, 0) or 0) for it in m1_module.PRODUCE_TO_DROP)
                if produce_load > 0 and (hour >= 20 or produce_load >= 5 or m1_module._dist(pos, ns) <= 2):
                    actions[w] = [m1_module._bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]

        return actions


# 2. Counterfactual B: Quota 50 + M1 Cow Purchasing Timing (Cap Day 6 cow buy at 1)
class Quota50M1CowTimingAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        # Enforce M1 cow purchase cap: on day 6, buy at most 1 cow
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

def evaluate_match(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_one(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        sold = {"WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0}
        for st in steps:
            for o in (st[0].get("action") or {}).get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    if o[1] in sold: sold[o[1]] += o[2]
        return {
            "reward": steps[-1][0]["reward"],
            "sold": sold
        }

    m1 = run_one(m1_module.ClosedLoopEconomicV1())
    q50 = run_one(ParameterizedQuotaAgent(50))
    cf_slot = run_one(SheepSlotPreservationAgent(50))
    cf_cow = run_one(Quota50M1CowTimingAgent(50))

    return {
        "seed": seed,
        "m1": m1,
        "q50": q50,
        "cf_slot": cf_slot,
        "cf_cow": cf_cow
    }

def main():
    seeds = list(range(1000, 1020)) # 20 seeds
    print(f"Running pasture counterfactuals across {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(evaluate_match, seeds))

    print(f"\n{'Seed':<6} | {'M1 Rew':<9} {'Q50 Rew':<9} {'CF_Slot':<9} {'CF_Cow':<9} | {'Diff Slot':<10} {'Diff Cow':<10} | {'Wool: M1/Q50/Slot/Cow'}")
    slot_diffs, cow_diffs = [], []
    wool_m1, wool_q50, wool_slot, wool_cow = [], [], [], []
    wheat_m1, wheat_q50, wheat_slot, wheat_cow = [], [], [], []

    for r in results:
        m1_r = r["m1"]["reward"]
        q50_r = r["q50"]["reward"]
        sl_r = r["cf_slot"]["reward"]
        cw_r = r["cf_cow"]["reward"]
        d_sl = sl_r - m1_r
        d_cw = cw_r - m1_r
        slot_diffs.append(d_sl)
        cow_diffs.append(d_cw)
        
        w_m = r["m1"]["sold"]["WOOL"]
        w_q = r["q50"]["sold"]["WOOL"]
        w_sl = r["cf_slot"]["sold"]["WOOL"]
        w_cw = r["cf_cow"]["sold"]["WOOL"]
        wool_m1.append(w_m); wool_q50.append(w_q); wool_slot.append(w_sl); wool_cow.append(w_cw)

        wh_m = r["m1"]["sold"]["WHEAT"]
        wh_q = r["q50"]["sold"]["WHEAT"]
        wh_sl = r["cf_slot"]["sold"]["WHEAT"]
        wh_cw = r["cf_cow"]["sold"]["WHEAT"]
        wheat_m1.append(wh_m); wheat_q50.append(wh_q); wheat_slot.append(wh_sl); wheat_cow.append(wh_cw)

        print(f"{r['seed']:<6} | {m1_r:<9,.0f} {q50_r:<9,.0f} {sl_r:<9,.0f} {cw_r:<9,.0f} | {d_sl:<+10,.0f} {d_cw:<+10,.0f} | {w_m}/{w_q}/{w_sl}/{w_cw}")

    print("\n=== SUMMARY ACROSS 20 SEEDS ===")
    print(f"M1 Mean Reward:       ${np.mean([r['m1']['reward'] for r in results]):,.2f}")
    print(f"Q50 Mean Reward:      ${np.mean([r['q50']['reward'] for r in results]):,.2f} (Delta: ${np.mean([r['q50']['reward']-r['m1']['reward'] for r in results]):+,.2f})")
    print(f"CF_Slot Mean Reward:  ${np.mean(slot_diffs)+np.mean([r['m1']['reward'] for r in results]):,.2f} (Delta vs M1: ${np.mean(slot_diffs):+,.2f})")
    print(f"CF_Cow Mean Reward:   ${np.mean(cow_diffs)+np.mean([r['m1']['reward'] for r in results]):,.2f} (Delta vs M1: ${np.mean(cow_diffs):+,.2f})")
    print()
    print(f"Mean Wool:  M1={np.mean(wool_m1):.1f} | Q50={np.mean(wool_q50):.1f} | CF_Slot={np.mean(wool_slot):.1f} | CF_Cow={np.mean(wool_cow):.1f}")
    print(f"Mean Wheat: M1={np.mean(wheat_m1):.1f} | Q50={np.mean(wheat_q50):.1f} | CF_Slot={np.mean(wheat_slot):.1f} | CF_Cow={np.mean(wheat_cow):.1f}")

if __name__ == "__main__":
    main()
