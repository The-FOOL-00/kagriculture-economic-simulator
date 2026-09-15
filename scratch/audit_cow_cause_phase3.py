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

def audit_seed_purchases(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_agent_and_track(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        cow_buys = []
        sheep_buys = []
        
        for step_idx, st in enumerate(steps):
            p0 = st[0]
            obs = p0.get("observation") or {}
            act = p0.get("action") or {}
            
            day = step_idx // 24
            hr = step_idx % 24
            
            market = act.get("market") or []
            farm = (obs.get("farms") or [{}, {}])[0]
            tiles = farm.get("tiles") or []
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            money_before = farm.get("money", 0)
            
            # Count current pasture occupancy
            cows_on_field = 0
            sheep_on_field = 0
            empty_pastures = 0
            for y in range(len(tiles)):
                for x in range(len(tiles[y])):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        if t.get("animal") == "COW": cows_on_field += 1
                        elif t.get("animal") == "SHEEP": sheep_on_field += 1
                        elif t.get("kind") == "PASTURE" and not t.get("animal"): empty_pastures += 1

            for o in market:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL":
                    sp = o[1]
                    qty = int(o[2])
                    cost = qty * (400 if sp == "COW" else 500)
                    money_after = money_before - cost
                    info = {
                        "day": day,
                        "hour": hr,
                        "step": step_idx,
                        "qty": qty,
                        "money_before": money_before,
                        "money_after": money_after,
                        "cows_on_field": cows_on_field,
                        "sheep_on_field": sheep_on_field,
                        "empty_pastures": empty_pastures,
                        "shed_sheep": shed.get("SHEEP", 0),
                        "shed_cow": shed.get("COW", 0)
                    }
                    if sp == "COW":
                        cow_buys.append(info)
                    elif sp == "SHEEP":
                        sheep_buys.append(info)

        rew = steps[-1][0]["reward"]
        
        # Summary metrics
        first_cow_day = cow_buys[0]["day"] if cow_buys else -1
        # Day 0 is initial purchase (3 cows, 1 sheep); find first post-day-0 cow purchase
        post_d0_cow_buys = [b for b in cow_buys if b["day"] > 0]
        first_mid_cow_day = post_d0_cow_buys[0]["day"] if post_d0_cow_buys else -1
        last_cow_day = cow_buys[-1]["day"] if cow_buys else -1
        total_cows_bought = sum(b["qty"] for b in cow_buys)

        first_sheep_day = sheep_buys[0]["day"] if sheep_buys else -1
        post_d0_sheep_buys = [b for b in sheep_buys if b["day"] > 0]
        first_mid_sheep_day = post_d0_sheep_buys[0]["day"] if post_d0_sheep_buys else -1
        last_sheep_day = sheep_buys[-1]["day"] if sheep_buys else -1
        total_sheep_bought = sum(b["qty"] for b in sheep_buys)

        return {
            "reward": rew,
            "cow_buys": cow_buys,
            "sheep_buys": sheep_buys,
            "first_mid_cow_day": first_mid_cow_day,
            "last_cow_day": last_cow_day,
            "total_cows_bought": total_cows_bought,
            "first_mid_sheep_day": first_mid_sheep_day,
            "last_sheep_day": last_sheep_day,
            "total_sheep_bought": total_sheep_bought
        }

    m1_data = run_agent_and_track(m1_module.ClosedLoopEconomicV1())
    q50_data = run_agent_and_track(ParameterizedQuotaAgent(50))

    return {
        "seed": seed,
        "m1": m1_data,
        "q50": q50_data
    }

def main():
    seeds = list(range(1050, 1150)) # 100 validation seeds
    print(f"Running Phase 3 audit across {len(seeds)} validation seeds (Seeds 1050-1149)...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(audit_seed_purchases, seeds))

    m1_first_cow = [r["m1"]["first_mid_cow_day"] for r in results if r["m1"]["first_mid_cow_day"] > 0]
    q50_first_cow = [r["q50"]["first_mid_cow_day"] for r in results if r["q50"]["first_mid_cow_day"] > 0]

    m1_first_sheep = [r["m1"]["first_mid_sheep_day"] for r in results if r["m1"]["first_mid_sheep_day"] > 0]
    q50_first_sheep = [r["q50"]["first_mid_sheep_day"] for r in results if r["q50"]["first_mid_sheep_day"] > 0]

    cow_shifts = []
    sheep_shifts = []
    for r in results:
        if r["m1"]["first_mid_cow_day"] > 0 and r["q50"]["first_mid_cow_day"] > 0:
            cow_shifts.append(r["q50"]["first_mid_cow_day"] - r["m1"]["first_mid_cow_day"])
        if r["m1"]["first_mid_sheep_day"] > 0 and r["q50"]["first_mid_sheep_day"] > 0:
            sheep_shifts.append(r["q50"]["first_mid_sheep_day"] - r["m1"]["first_mid_sheep_day"])

    cow_shifts = np.array(cow_shifts)
    sheep_shifts = np.array(sheep_shifts)

    t_cow, p_cow = stats.ttest_1samp(cow_shifts, 0.0)
    t_sheep, p_sheep = stats.ttest_1samp(sheep_shifts, 0.0)

    summary = {
        "n_seeds": len(results),
        "m1_mean_first_cow_day": round(float(np.mean(m1_first_cow)), 2),
        "q50_mean_first_cow_day": round(float(np.mean(q50_first_cow)), 2),
        "mean_cow_timing_shift": round(float(np.mean(cow_shifts)), 2),
        "p_value_cow_shift": round(float(p_cow), 4),
        "m1_mean_first_sheep_day": round(float(np.mean(m1_first_sheep)), 2),
        "q50_mean_first_sheep_day": round(float(np.mean(q50_first_sheep)), 2),
        "mean_sheep_timing_shift": round(float(np.mean(sheep_shifts)), 2),
        "p_value_sheep_shift": round(float(p_sheep), 4),
    }

    with open("scratch/phase3_cow_cause_results.json", "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("\n=== PHASE 3 AUDIT RESULTS ===")
    print(f"M1 Mean First Cow Day (post D0):  Day {summary['m1_mean_first_cow_day']}")
    print(f"Q50 Mean First Cow Day (post D0): Day {summary['q50_mean_first_cow_day']}")
    print(f"Mean Cow Timing Shift (Q50 - M1): {summary['mean_cow_timing_shift']:+.2f} days (p = {summary['p_value_cow_shift']:.4f})")
    print(f"M1 Mean First Sheep Day (post D0):  Day {summary['m1_mean_first_sheep_day']}")
    print(f"Q50 Mean First Sheep Day (post D0): Day {summary['q50_mean_first_sheep_day']}")
    print(f"Mean Sheep Timing Shift (Q50 - M1): {summary['mean_sheep_timing_shift']:+.2f} days (p = {summary['p_value_sheep_shift']:.4f})")

if __name__ == "__main__":
    main()
