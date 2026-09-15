"""
scratch/audit_cms5_sweeps.py
============================
Executes exact empirical sweeps for:
- Section 4: wheat_seeds in [175, 180, 185, 187, 190, 195] on 10 seeds (101-110)
- Section 8: liquidation_step in [620, 630, 640, 645, 650, 655, 660, 670] on 30 seeds (101-130) both SOLO and VS V54
- Section 9: dense wheat sweep [170, 172, 174, 176, 178, 180, 182, 184, 185, 186, 187, 188, 190, 192, 195, 200] on 30 seeds (101-130)
Outputs structured results to JSON for rigorous reporting.
"""

import os
import sys
if os.path.abspath(".") not in sys.path:
    sys.path.insert(0, os.path.abspath("."))
import json
import time
import math
import importlib.util
from concurrent.futures import ProcessPoolExecutor
import numpy as np

def compute_stats(vals):
    n = len(vals)
    mean_val = float(np.mean(vals))
    median_val = float(np.median(vals))
    sd_val = float(np.std(vals, ddof=1)) if n > 1 else 0.0
    se = sd_val / math.sqrt(n) if n > 1 else 0.0
    ci_95 = 1.96 * se
    return {
        "mean": mean_val,
        "median": median_val,
        "sd": sd_val,
        "ci_low": mean_val - ci_95,
        "ci_high": mean_val + ci_95
    }

# Worker task function
def _eval_single_game(task):
    agent_cfg_dict, opp_type, seed, collect_telemetry = task
    from kaggle_environments import make
    from candidates.cms5_v54_faithful import build_cms5_policy, CMS5Config

    agent_cfg = CMS5Config(**agent_cfg_dict)
    agent_fn = build_cms5_policy(agent_cfg)

    if opp_type == "IDLE":
        opp_fn = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}
    else: # V54
        v54_path = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
        spec_v54 = importlib.util.spec_from_file_location(f"v54_{seed}_{os.getpid()}", v54_path)
        mod_v54 = importlib.util.module_from_spec(spec_v54)
        spec_v54.loader.exec_module(mod_v54)
        opp_fn = getattr(mod_v54, "agent")

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, opp_fn])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0) if opp_type == "V54" else 0.0

    telemetry = {}
    if collect_telemetry:
        # Measure wheat purchased, planted, harvested, sold, cash milestones, livestock uptime
        wheat_bought = 0
        wheat_feed_bought = 0
        wheat_planted = 0
        wheat_harvested = 0
        wheat_sold = 0
        cash_d5 = 0.0
        cash_d10 = 0.0
        cash_d15 = 0.0
        livestock_fed_events = 0
        total_animal_days = 0

        for s in env.steps[1:]:
            step_idx = s[0].observation.step
            farm = s[0].observation.farms[0]
            money = float(farm.get("money", 0.0))

            if step_idx == 120: cash_d5 = money
            elif step_idx == 240: cash_d10 = money
            elif step_idx == 360: cash_d15 = money

            act = s[0].action or {}
            for o in act.get("market", []):
                if not o: continue
                if o[0] == "BUY_SEED" and o[1] == "WHEAT":
                    wheat_bought += o[2]
                elif o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                    wheat_feed_bought += o[2]
                elif o[0] == "SELL" and o[1] == "WHEAT":
                    wheat_sold += o[2]

            for h in act.get("hands", []):
                if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "WHEAT":
                    wheat_planted += 1
                elif h and h[0] == "HARVEST":
                    wheat_harvested += 1 # approximate harvest actions

            # Check animal fed
            for row in farm.get("tiles", []):
                for tile in row:
                    if isinstance(tile, dict) and "animal" in tile:
                        total_animal_days += 1
                        if tile.get("fed_today", False):
                            livestock_fed_events += 1

        telemetry = {
            "wheat_bought": wheat_bought,
            "wheat_feed_bought": wheat_feed_bought,
            "wheat_planted": wheat_planted,
            "wheat_harvested": wheat_harvested,
            "wheat_sold": wheat_sold,
            "cash_d5": cash_d5,
            "cash_d10": cash_d10,
            "cash_d15": cash_d15,
            "livestock_uptime": livestock_fed_events / max(1, total_animal_days) * 100.0
        }

    return {
        "cfg": agent_cfg_dict,
        "opp_type": opp_type,
        "seed": seed,
        "r0": r0,
        "r1": r1,
        "margin": r0 - r1 if opp_type == "V54" else r0,
        "win": 1 if r0 > r1 else 0,
        "telemetry": telemetry
    }

def run_section_4():
    print("=" * 80)
    print("SECTION 4: WHEAT SEED PARAMETER WIRING TEST (10 SEEDS: 101-110)")
    print("=" * 80)
    seeds = list(range(101, 111))
    wheat_vals = [175, 180, 185, 187, 190, 195]
    tasks = []
    for w in wheat_vals:
        for s in seeds:
            tasks.append(({"wheat_seeds": w}, "IDLE", s, False))

    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_eval_single_game, tasks))

    # Organize per-seed table
    res_by_val = {w: {} for w in wheat_vals}
    for r in results:
        w = r["cfg"]["wheat_seeds"]
        s = r["seed"]
        res_by_val[w][s] = r["r0"]

    print(f"{'Seed':6s} | " + " | ".join(f"w={w:<7d}" for w in wheat_vals))
    print("-" * 65)
    for s in seeds:
        row_str = f"{s:<6d} | "
        for w in wheat_vals:
            row_str += f"${res_by_val[w][s]:<8,.0f} | "
        print(row_str)

    # Save to file
    with open("scratch/section4_wheat_wiring.json", "w") as f:
        json.dump(res_by_val, f, indent=2)

def run_section_8():
    print("\n" + "=" * 80)
    print("SECTION 8: LIQUIDATION TIMING CONTRADICTION (30 SEEDS: 101-130)")
    print("=" * 80)
    seeds = list(range(101, 131))
    liq_steps = [620, 630, 640, 645, 650, 655, 660, 670]
    tasks_solo = []
    tasks_comp = []
    for l in liq_steps:
        for s in seeds:
            tasks_solo.append(({"liquidation_step": l}, "IDLE", s, False))
            tasks_comp.append(({"liquidation_step": l}, "V54", s, False))

    with ProcessPoolExecutor(max_workers=8) as executor:
        res_solo = list(executor.map(_eval_single_game, tasks_solo))
        res_comp = list(executor.map(_eval_single_game, tasks_comp))

    solo_by_step = {l: [r["r0"] for r in res_solo if r["cfg"]["liquidation_step"] == l] for l in liq_steps}
    comp_by_step = {l: [r["margin"] for r in res_comp if r["cfg"]["liquidation_step"] == l] for l in liq_steps}
    wins_by_step = {l: sum(r["win"] for r in res_comp if r["cfg"]["liquidation_step"] == l) for l in liq_steps}

    base_solo = solo_by_step[670]
    base_comp = comp_by_step[670]

    print("\n--- SOLO EVALUATION VS IDLE ---")
    print(f"{'LiqStep':8s} | {'Mean':>10s} | {'Median':>10s} | {'Delta vs 670':>13s} | {'95% CI':>22s}")
    print("-" * 75)
    solo_stats = {}
    for l in liq_steps:
        st = compute_stats(solo_by_step[l])
        deltas = [a - b for a, b in zip(solo_by_step[l], base_solo)]
        dst = compute_stats(deltas)
        solo_stats[l] = {"abs": st, "delta": dst}
        print(f"{l:<8d} | ${st['mean']:>9,.0f} | ${st['median']:>9,.0f} | ${dst['mean']:>+12,.1f} | [${dst['ci_low']:>+9,.1f}, ${dst['ci_high']:>+9,.1f}]")

    print("\n--- COMPETITIVE EVALUATION VS V54 ---")
    print(f"{'LiqStep':8s} | {'Mean Margin':>12s} | {'Median Margin':>14s} | {'Delta vs 670':>13s} | {'95% CI':>22s} | {'WinRate':>8s}")
    print("-" * 88)
    comp_stats = {}
    for l in liq_steps:
        st = compute_stats(comp_by_step[l])
        deltas = [a - b for a, b in zip(comp_by_step[l], base_comp)]
        dst = compute_stats(deltas)
        wr = wins_by_step[l] / len(seeds) * 100.0
        comp_stats[l] = {"margin": st, "delta": dst, "win_rate": wr}
        print(f"{l:<8d} | ${st['mean']:>11,.0f} | ${st['median']:>13,.0f} | ${dst['mean']:>+12,.1f} | [${dst['ci_low']:>+9,.1f}, ${dst['ci_high']:>+9,.1f}] | {wr:>7.1f}%")

    with open("scratch/section8_liquidation_results.json", "w") as f:
        json.dump({"solo": solo_stats, "comp": comp_stats}, f, indent=2)

def run_section_9():
    print("\n" + "=" * 80)
    print("SECTION 9: DENSE WHEAT SWEEP (30 SEEDS: 101-130)")
    print("=" * 80)
    seeds = list(range(101, 131))
    wheat_vals = [170, 172, 174, 176, 178, 180, 182, 184, 185, 186, 187, 188, 190, 192, 195, 200]
    tasks = []
    for w in wheat_vals:
        for s in seeds:
            tasks.append(({"wheat_seeds": w}, "IDLE", s, True))

    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_eval_single_game, tasks))

    summary_by_w = {}
    print(f"{'Wheat':6s} | {'Reward Mean':>11s} | {'Median':>9s} | {'FeedBought':>11s} | {'WheatSold':>10s} | {'Cash D5':>8s} | {'Cash D10':>9s} | {'Cash D15':>9s} | {'95% CI':>22s}")
    print("-" * 115)
    for w in wheat_vals:
        sub = [r for r in results if r["cfg"]["wheat_seeds"] == w]
        rews = [r["r0"] for r in sub]
        st = compute_stats(rews)
        feed_b = float(np.mean([r["telemetry"]["wheat_feed_bought"] for r in sub]))
        w_sold = float(np.mean([r["telemetry"]["wheat_sold"] for r in sub]))
        c5 = float(np.mean([r["telemetry"]["cash_d5"] for r in sub]))
        c10 = float(np.mean([r["telemetry"]["cash_d10"] for r in sub]))
        c15 = float(np.mean([r["telemetry"]["cash_d15"] for r in sub]))

        summary_by_w[w] = {
            "stats": st,
            "feed_bought": feed_b,
            "wheat_sold": w_sold,
            "cash_d5": c5,
            "cash_d10": c10,
            "cash_d15": c15
        }
        print(f"{w:<6d} | ${st['mean']:>10,.0f} | ${st['median']:>8,.0f} | {feed_b:>11.1f} | {w_sold:>10.1f} | ${c5:>7,.0f} | ${c10:>8,.0f} | ${c15:>8,.0f} | [${st['ci_low']:>9,.0f}, ${st['ci_high']:>9,.0f}]")

    with open("scratch/section9_dense_wheat_results.json", "w") as f:
        json.dump(summary_by_w, f, indent=2)

if __name__ == "__main__":
    t0 = time.time()
    run_section_4()
    run_section_8()
    run_section_9()
    print(f"\nAll sweeps completed in {time.time()-t0:.1f}s")
