"""
scratch/independent_cms5_verifier.py
====================================
Independent verification harness for CMS-5 Championship results.
Strictly decoupled from scratch/cms5_v54_plus_eval.py.

Runs:
1. CMS5_187 vs V54 (Seat 0 and Seat 1)
2. CMS5_185 vs V54 (Seat 0 and Seat 1)
Across:
- 50 Validation seeds (101-150)
- 100 Blind seeds (501-600)

Records all required per-match columns:
seed, seat, candidate, CMS5 reward, V54 reward, margin, CMS5 final cash, V54 final cash,
wheat purchased, wheat planted, wheat harvested, wheat sold, total sales, terminal inventory.

Computes exact statistical distributions and verifies seat symmetry.
"""

import os
import sys
if os.path.abspath(".") not in sys.path:
    sys.path.insert(0, os.path.abspath("."))
import csv
import json
import time
import math
import importlib.util
from concurrent.futures import ProcessPoolExecutor
import numpy as np

def run_single_h2h_match(task):
    candidate_wheat_seeds, candidate_seat, seed = task
    from kaggle_environments import make

    from candidates.cms5_v54_faithful import build_cms5_policy, CMS5Config
    cms5_agent = build_cms5_policy(CMS5Config(wheat_seeds=candidate_wheat_seeds))

    # Load canonical V54
    v54_path = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    spec_v54 = importlib.util.spec_from_file_location(f"v54_ind_{os.getpid()}", v54_path)
    mod_v54 = importlib.util.module_from_spec(spec_v54)
    sys.modules[f"v54_ind_{os.getpid()}"] = mod_v54
    spec_v54.loader.exec_module(mod_v54)
    v54_agent = getattr(mod_v54, "agent")

    if candidate_seat == 0:
        agents = [cms5_agent, v54_agent]
        cand_idx = 0
        v54_idx = 1
    else:
        agents = [v54_agent, cms5_agent]
        cand_idx = 1
        v54_idx = 0

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run(agents)

    r_cand = float(env.steps[-1][cand_idx].reward or 0.0)
    r_v54 = float(env.steps[-1][v54_idx].reward or 0.0)
    margin = r_cand - r_v54

    cand_farm = env.steps[-1][cand_idx].observation.farms[cand_idx]
    v54_farm = env.steps[-1][v54_idx].observation.farms[v54_idx]
    cand_cash = float(cand_farm.get("money", 0.0))
    v54_cash = float(v54_farm.get("money", 0.0))

    cand_shed = cand_farm.get("shed", {})
    term_inv = sum(cand_shed.values())

    wheat_purchased = 0
    wheat_planted = 0
    wheat_harvested = 0
    wheat_sold = 0
    total_sales = 0.0

    for s in env.steps[1:]:
        act = s[cand_idx].action or {}
        obs_m = s[cand_idx].observation.market
        prices = obs_m.get("prices", {})

        for o in act.get("market", []):
            if not o: continue
            if o[0] == "BUY_SEED" and len(o) > 2 and o[1] == "WHEAT":
                wheat_purchased += o[2]
            elif o[0] == "SELL" and len(o) > 2:
                item = o[1]
                qty = o[2]
                pr = prices.get(item, 0.0)
                total_sales += qty * pr
                if item == "WHEAT":
                    wheat_sold += qty

        for h in act.get("hands", []):
            if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "WHEAT":
                wheat_planted += 1
            elif h and h[0] == "HARVEST":
                wheat_harvested += 1

    return {
        "candidate": f"CMS5_{candidate_wheat_seeds}",
        "wheat_param": candidate_wheat_seeds,
        "seat": candidate_seat,
        "seed": seed,
        "cms5_reward": r_cand,
        "v54_reward": r_v54,
        "margin": margin,
        "cms5_final_cash": cand_cash,
        "v54_final_cash": v54_cash,
        "wheat_purchased": wheat_purchased,
        "wheat_planted": wheat_planted,
        "wheat_harvested": wheat_harvested,
        "wheat_sold": wheat_sold,
        "total_sales": total_sales,
        "terminal_inventory": term_inv
    }


def analyze_deltas(deltas):
    arr = np.array(deltas, dtype=float)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    sd_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se = sd_val / math.sqrt(len(arr)) if len(arr) > 1 else 0.0
    ci_low = mean_val - 1.96 * se
    ci_high = mean_val + 1.96 * se

    # Mode
    vals, counts = np.unique(arr, return_counts=True)
    mode_val = float(vals[np.argmax(counts)])

    percentiles = {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": mean_val,
        "median": median_val,
        "mode": mode_val,
        "p01": float(np.percentile(arr, 1)),
        "p05": float(np.percentile(arr, 5)),
        "p10": float(np.percentile(arr, 10)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "std": sd_val,
        "ci_95": [ci_low, ci_high]
    }
    return percentiles


def main():
    print("=" * 80)
    print("INDEPENDENT CMS-5 CHAMPIONSHIP VERIFICATION PROTOCOL")
    print("=" * 80)

    val_seeds = list(range(101, 151))   # 50 validation seeds
    blind_seeds = list(range(501, 601)) # 100 blind seeds

    all_tasks = []

    # 1. Validation Seeds: CMS5_187 vs V54 (Seat 0 & Seat 1)
    for s in val_seeds:
        all_tasks.append((187, 0, s))
        all_tasks.append((187, 1, s))
    # 2. Validation Seeds: CMS5_185 vs V54 (Seat 0 & Seat 1)
    for s in val_seeds:
        all_tasks.append((185, 0, s))
        all_tasks.append((185, 1, s))

    # 3. Blind Seeds: CMS5_187 vs V54 (Seat 0 & Seat 1)
    for s in blind_seeds:
        all_tasks.append((187, 0, s))
        all_tasks.append((187, 1, s))
    # 4. Blind Seeds: CMS5_185 vs V54 (Seat 0 & Seat 1)
    for s in blind_seeds:
        all_tasks.append((185, 0, s))
        all_tasks.append((185, 1, s))

    print(f"Total verification matches to execute: {len(all_tasks)} (using 10 parallel workers)...", flush=True)
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_single_h2h_match, all_tasks))

    elapsed = time.time() - t0
    print(f"Executed {len(results)} matches in {elapsed:.1f}s ({elapsed/len(results):.2f}s/match)\n")

    # Save complete raw per-match table to CSV
    csv_file = "scratch/independent_cms5_raw_matches.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved complete per-match table to {csv_file}")

    # Now partition and analyze
    partitions = {
        "VALIDATION": val_seeds,
        "BLIND": blind_seeds
    }

    summary_stats = {}

    for part_name, seeds in partitions.items():
        print(f"\n{'='*30} {part_name} PARTITION ({len(seeds)} SEEDS) {'='*30}")
        for w in [187, 185]:
            cand_name = f"CMS5_{w}"
            # Seat 0 matches
            m_s0 = [r for r in results if r["wheat_param"] == w and r["seat"] == 0 and r["seed"] in seeds]
            # Seat 1 matches
            m_s1 = [r for r in results if r["wheat_param"] == w and r["seat"] == 1 and r["seed"] in seeds]

            margins_s0 = [r["margin"] for r in m_s0]
            margins_s1 = [r["margin"] for r in m_s1]
            pooled_margins = [(r0["margin"] + r1["margin"]) / 2.0 for r0, r1 in zip(m_s0, m_s1)]

            wins_s0 = sum(1 for m in margins_s0 if m > 0)
            ties_s0 = sum(1 for m in margins_s0 if m == 0)
            losses_s0 = sum(1 for m in margins_s0 if m < 0)

            wins_s1 = sum(1 for m in margins_s1 if m > 0)
            ties_s1 = sum(1 for m in margins_s1 if m == 0)
            losses_s1 = sum(1 for m in margins_s1 if m < 0)

            dist_s0 = analyze_deltas(margins_s0)
            dist_s1 = analyze_deltas(margins_s1)
            dist_pooled = analyze_deltas(pooled_margins)

            print(f"\n--- {cand_name} vs V54 [{part_name}] ---")
            print(f"Seat 0 Margin: Mean=${dist_s0['mean']:+,.2f} | Median=${dist_s0['median']:+,.2f} | Record: {wins_s0}W/{ties_s0}T/{losses_s0}L ({wins_s0/len(seeds)*100:.1f}%)")
            print(f"Seat 1 Margin: Mean=${dist_s1['mean']:+,.2f} | Median=${dist_s1['median']:+,.2f} | Record: {wins_s1}W/{ties_s1}T/{losses_s1}L ({wins_s1/len(seeds)*100:.1f}%)")
            print(f"Symmetric Pooled: Mean=${dist_pooled['mean']:+,.2f} | Median=${dist_pooled['median']:+,.2f} | 95% CI: [${dist_pooled['ci_95'][0]:+,.2f}, ${dist_pooled['ci_95'][1]:+,.2f}] | SD=${dist_pooled['std']:,.2f}")

            summary_stats[f"{part_name}_{cand_name}"] = {
                "seat_0": {"stats": dist_s0, "record": f"{wins_s0}W/{ties_s0}T/{losses_s0}L"},
                "seat_1": {"stats": dist_s1, "record": f"{wins_s1}W/{ties_s1}T/{losses_s1}L"},
                "pooled_symmetric": {"stats": dist_pooled}
            }

    # Save summary stats to JSON
    with open("scratch/independent_cms5_summary.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("\nVerification analysis saved to scratch/independent_cms5_summary.json")

if __name__ == "__main__":
    main()
