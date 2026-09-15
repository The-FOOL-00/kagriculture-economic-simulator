import json
import os
import sys
import time
import argparse
import numpy as np
from collections import defaultdict
from scipy import stats
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_fert_gated import agent as m1_agent
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

SEEDS_100_FRESH = list(range(1050, 1150))

def run_match_fresh(args):
    arm_name, quota, seed = args
    if arm_name == "M1":
        agent_fn = m1_agent
    elif arm_name == "BestQuota":
        agent_fn = ParameterizedQuotaAgent(quota)
    else:
        raise ValueError(f"Unknown arm {arm_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent_fn, "starter"])
    p = 0

    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    exp_seeds = 0.0
    exp_feed = 0.0
    moves = 0
    passes = 0

    wheat_planted = 0
    wheat_harvested = 0
    straw_planted = 0
    straw_harvested = 0
    straw_fertilized = 0

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][p]["observation"]
        curr_obs = steps[s_idx][p]["observation"]
        prev_farm = prev_obs["farms"][p]
        curr_farm = curr_obs["farms"][p]
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
        for wact in all_wacts:
            if not wact:
                passes += 1
                continue
            op = wact[0] if isinstance(wact, list) and len(wact) > 0 else (wact if isinstance(wact, str) else "PASS")
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                moves += 1
            elif op == "PASS":
                passes += 1

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
                    wheat_planted += 1

                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    p_fert = pt.get("fertilized_until_day", -1)
                    c_fert = ct.get("fertilized_until_day", -1) if isinstance(ct, dict) else -1
                    if c_fert > p_fert and c_fert >= day:
                        straw_fertilized += 1
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "STRAWBERRY" else 0
                    if py > cy and [c, r] in workers:
                        straw_harvested += (py - cy)

                if isinstance(pt, dict) and pt.get("crop") == "WHEAT":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "WHEAT" else 0
                    if py > cy and [c, r] in workers:
                        wheat_harvested += (py - cy)

    last_farm = steps[-1][p]["observation"]["farms"][p]
    terminal_reward = float(last_farm.get("money") or 0.0)

    return {
        "arm": arm_name,
        "quota": quota,
        "seed": seed,
        "terminal_reward": terminal_reward,
        "wheat_planted": wheat_planted,
        "wheat_harvested": wheat_harvested,
        "wheat_sold": qty_sold["WHEAT"],
        "wheat_rev": rev_by_item["WHEAT"],
        "straw_sold": qty_sold["STRAWBERRY"],
        "straw_harvested": straw_harvested,
        "straw_fertilized": straw_fertilized,
        "wool_sold": qty_sold["WOOL"],
        "milk_sold": qty_sold["MILK"],
        "melon_sold": qty_sold["MELON"],
        "fert_sold": qty_sold["FERTILIZER"],
        "exp_seeds": exp_seeds,
        "exp_feed": exp_feed,
        "moves": moves,
        "passes": passes
    }

def run_validation(quota):
    print(f"Executing 100-Seed Validation for Quota {quota} vs M1 on Seeds 1050-1149...")
    tasks = []
    for s in SEEDS_100_FRESH:
        tasks.append(("M1", quota, s))
        tasks.append(("BestQuota", quota, s))

    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(run_match_fresh, tasks):
            results.append(res)
            if len(results) % 40 == 0:
                print(f"Processed {len(results)}/{len(tasks)} runs ({time.time()-t0:.1f}s)...", flush=True)

    out_file = f"scratch/validation_quota_{quota}_100seeds_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    # Compute exact statistics
    m1_data = {r["seed"]: r for r in results if r["arm"] == "M1"}
    cand_data = {r["seed"]: r for r in results if r["arm"] == "BestQuota"}

    m1_rews = np.array([m1_data[s]["terminal_reward"] for s in SEEDS_100_FRESH])
    cand_rews = np.array([cand_data[s]["terminal_reward"] for s in SEEDS_100_FRESH])
    delta = cand_rews - m1_rews

    m1_m = np.mean(m1_rews)
    cand_m = np.mean(cand_rews)
    d_m = np.mean(delta)
    d_med = np.median(delta)
    d_sd = np.std(delta, ddof=1)
    win_rate = np.mean(delta > 0) * 100.0

    # 95% Bootstrap CI
    rng = np.random.default_rng(42)
    boot_means = [np.mean(rng.choice(delta, size=len(delta), replace=True)) for _ in range(10000)]
    ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])

    # Paired permutation p-value (10,000 permutations)
    signs = rng.choice([-1, 1], size=(10000, len(delta)))
    perm_means = np.mean(signs * delta, axis=1)
    perm_p = np.mean(np.abs(perm_means) >= np.abs(d_m))

    # Cohen's d effect size
    cohen_d = d_m / d_sd if d_sd > 0 else 0.0

    print("\n" + "="*80)
    print(f"100-SEED FRESH VALIDATION RESULTS: M1 vs Best Quota ({quota})")
    print("="*80)
    print(f"M1 Baseline Mean:      ${m1_m:.2f} (Median: ${np.median(m1_rews):.2f}, SD: ${np.std(m1_rews, ddof=1):.2f})")
    print(f"Best Quota ({quota}) Mean: ${cand_m:.2f} (Median: ${np.median(cand_rews):.2f}, SD: ${np.std(cand_rews, ddof=1):.2f})")
    print(f"Delta Mean:            ${d_m:+.2f}")
    print(f"Delta Median:          ${d_med:+.2f}")
    print(f"Delta Std Dev:         ${d_sd:.2f}")
    print(f"95% Bootstrap CI:      [${ci_low:+.2f}, ${ci_high:+.2f}]")
    print(f"Paired Permutation p:  {perm_p:.4f}")
    print(f"Win Rate:              {win_rate:.1f}%")
    print(f"Effect Size (Cohen d): {cohen_d:.4f}")

    # Commodity deltas
    print("\nCommodity Physical & Financial Deltas (Best Quota - M1):")
    for comm in ["wheat_sold", "wheat_harvested", "straw_sold", "straw_harvested", "wool_sold", "milk_sold", "melon_sold", "fert_sold"]:
        m1_c = np.mean([m1_data[s][comm] for s in SEEDS_100_FRESH])
        c_c = np.mean([cand_data[s][comm] for s in SEEDS_100_FRESH])
        print(f"  {comm:<16}: M1 = {m1_c:6.1f}, Quota = {c_c:6.1f}, Delta = {c_c - m1_c:+6.1f}")

    return {
        "quota": quota,
        "m1_mean": m1_m,
        "cand_mean": cand_m,
        "delta_mean": d_m,
        "delta_median": d_med,
        "delta_sd": d_sd,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "perm_p": perm_p,
        "win_rate": win_rate,
        "cohen_d": cohen_d
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quota", type=int, default=50)
    args = parser.parse_args()
    run_validation(args.quota)
