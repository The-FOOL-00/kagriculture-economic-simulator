"""
TARGETED FORENSIC DECOMPOSITION — Straw-only vs Pizza+Straw
===========================================================
Identifies the mechanism behind V2's underperformance in Straw-only worlds
(WR=27-47%) vs Pizza+Straw worlds (WR=57-61%).

Uses the margin scan results to identify seeds by shop family, then runs
the full forensic logger on each group to decompose the delta.
"""

import sys, os, json, time
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
SCRATCH = os.path.join(BASE_DIR, "scratch")


def _forensic_worker(seed, v2_seat):
    import sys, os, importlib.util
    sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
    sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
    sys.path.insert(0, DMITRII_DIR)
    sys.path.insert(0, SCRATCH)
    from forensic_logger_v2 import play_forensic_match
    return play_forensic_match(seed, v2_seat)


def run_group(seeds, label, max_workers=6):
    """Run CRN paired forensic matches for a set of seeds."""
    tasks = [(s, 0) for s in seeds] + [(s, 1) for s in seeds]
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(_forensic_worker, s, seat): (s, seat) for s, seat in tasks}
        for fut in as_completed(futures):
            s, seat = futures[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                print(f"  ERROR seed={s} seat={seat}: {e}")
    return results


def group_by_seed(results):
    by_seed = defaultdict(dict)
    for r in results:
        by_seed[r["seed"]][r["v2_seat"]] = r
    return by_seed


def compute_combined(by_seed):
    combined = {}
    for seed, seats in by_seed.items():
        g0 = seats.get(0)
        g1 = seats.get(1)
        if g0 and g1:
            combined[seed] = {
                "combined_margin": round(g0["paired_margin"] + g1["paired_margin"], 2),
                "g0": g0, "g1": g1,
            }
    return combined


def aggregate_econ(results):
    """Aggregate economic totals across a set of matches."""
    v2_totals = defaultdict(float)
    dm_totals = defaultdict(float)
    count = 0

    for r in results:
        v2 = r["v2"]
        dm = r["dm"]
        count += 1

        # Costs
        for k in ["cost_land", "cost_feed", "total_hires", "total_harvests",
                  "total_waters", "total_fertilizes", "total_passes",
                  "net_income", "implied_total_revenue", "explicit_costs"]:
            v2_totals[k] += float(v2.get(k, 0))
            dm_totals[k] += float(dm.get(k, 0))

        # Plants by crop
        for crop, cnt in v2.get("total_plants", {}).items():
            v2_totals[f"plants_{crop}"] += cnt
        for crop, cnt in dm.get("total_plants", {}).items():
            dm_totals[f"plants_{crop}"] += cnt

        # Sell qty by commodity
        for comm, cnt in v2.get("total_sells_qty", {}).items():
            v2_totals[f"sells_{comm}"] += cnt
        for comm, cnt in dm.get("total_sells_qty", {}).items():
            dm_totals[f"sells_{comm}"] += cnt

        # Seeds costs by crop
        for crop, cost in v2.get("cost_seeds", {}).items():
            v2_totals[f"seed_cost_{crop}"] += cost
        for crop, cost in dm.get("cost_seeds", {}).items():
            dm_totals[f"seed_cost_{crop}"] += cost

    if count == 0:
        return {}, {}, {}

    # Normalize to per-game averages
    v2_avg = {k: round(v / count, 2) for k, v in v2_totals.items()}
    dm_avg = {k: round(v / count, 2) for k, v in dm_totals.items()}

    # Delta (V2 - Dm)
    all_keys = set(list(v2_avg.keys()) + list(dm_avg.keys()))
    delta = {k: round(v2_avg.get(k, 0) - dm_avg.get(k, 0), 2) for k in all_keys}

    return v2_avg, dm_avg, delta


def analyze_group(results, label):
    by_seed = group_by_seed(results)
    combined = compute_combined(by_seed)
    margins = [v["combined_margin"] for v in combined.values()]
    n = len(margins)
    if n == 0:
        print(f"\n{label}: NO DATA")
        return

    import math
    mean_m = sum(margins) / n
    sorted_m = sorted(margins)
    std_m = math.sqrt(sum((m - mean_m)**2 for m in margins) / max(n-1, 1))
    se_m = std_m / math.sqrt(n)
    ci_lo = mean_m - 1.96 * se_m
    ci_hi = mean_m + 1.96 * se_m
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)

    print(f"\n{'='*60}")
    print(f"{label}  (N={n} seeds)")
    print(f"{'='*60}")
    print(f"  WR={wins/n*100:.0f}%  Mean={mean_m:+.0f}  CI=[{ci_lo:+.0f}, {ci_hi:+.0f}]")
    print(f"  Median={sorted_m[n//2]:+.0f}  Worst={sorted_m[0]:+.0f}  Best={sorted_m[-1]:+.0f}")

    # Economic decomposition
    v2_avg, dm_avg, delta = aggregate_econ(results)

    print(f"\n  Per-game averages (V2 vs Dmitrii):")
    for k in ["net_income", "implied_total_revenue", "explicit_costs",
              "cost_land", "cost_feed", "total_hires",
              "total_harvests", "total_waters", "total_fertilizes", "total_passes"]:
        v2v = v2_avg.get(k, 0)
        dmv = dm_avg.get(k, 0)
        dv = delta.get(k, 0)
        dir_str = "V2+" if dv > 5 else ("Dm+" if dv < -5 else "~")
        print(f"    {k:28s}: V2={v2v:>8.1f}  Dm={dmv:>8.1f}  d={dv:>+8.1f}  [{dir_str}]")

    print(f"\n  Plant counts (per game, V2 vs Dmitrii):")
    plant_keys = [k for k in delta if k.startswith("plants_")]
    for k in sorted(plant_keys):
        v2v = v2_avg.get(k, 0)
        dmv = dm_avg.get(k, 0)
        dv = delta.get(k, 0)
        dir_str = "V2+" if dv > 0.5 else ("Dm+" if dv < -0.5 else "~")
        print(f"    {k:28s}: V2={v2v:>6.1f}  Dm={dmv:>6.1f}  d={dv:>+5.1f}  [{dir_str}]")

    print(f"\n  Seed costs (per game, V2 vs Dmitrii):")
    seed_keys = [k for k in delta if k.startswith("seed_cost_")]
    for k in sorted(seed_keys):
        v2v = v2_avg.get(k, 0)
        dmv = dm_avg.get(k, 0)
        dv = delta.get(k, 0)
        dir_str = "V2+" if dv > 5 else ("Dm+" if dv < -5 else "~")
        print(f"    {k:28s}: V2={v2v:>8.1f}  Dm={dmv:>8.1f}  d={dv:>+8.1f}  [{dir_str}]")

    # Divergence analysis
    divs = [v["g0"]["divergence_day"] for v in combined.values() if v["g0"].get("divergence_day") is not None]
    if divs:
        print(f"\n  Divergence days (day where |cash gap| > $1000 for 2+ days):")
        from collections import Counter
        div_counts = Counter(divs)
        for day in sorted(div_counts):
            print(f"    Day {day:2d}: {div_counts[day]} games")
    else:
        print(f"\n  No divergence days found (gaps always < $1000)")

    # Loss game analysis
    loss_seeds = [(v["combined_margin"], s) for s, v in combined.items() if v["combined_margin"] < -100]
    if loss_seeds:
        print(f"\n  Loss seeds (combined margin < -100):")
        for m, s in sorted(loss_seeds):
            g0 = combined[s]["g0"]
            d = g0["delta"]
            traj = g0["gap_trajectory_daily"]
            print(f"    seed {s}: margin={m:+.0f}  rev_delta={d['implied_total_revenue']:+.0f}  "
                  f"cost_delta={d['explicit_costs']:+.0f}  "
                  f"hires={int(d['total_hires']):+d}  "
                  f"gap_traj={[round(x) for x in traj[:8]]}")

    return {"v2_avg": v2_avg, "dm_avg": dm_avg, "delta": delta, "margins": margins}


if __name__ == "__main__":
    # Load margin scan to get seed classifications
    scan = json.load(open(os.path.join(SCRATCH, "v2_dmitrii_margin_scan.json")))

    # Classify seeds by shop family from scan results
    straw_only_seeds = []
    pizza_straw_seeds = []

    for dataset in ["discovery", "qualification", "holdout"]:
        for r in scan[dataset]:
            if r["v2_seat"] != 0:
                continue  # Only take one record per seed for classification
            if r["shop_family"] == "Straw":
                straw_only_seeds.append(r["seed"])
            elif r["shop_family"] == "Pizza+Straw":
                pizza_straw_seeds.append(r["seed"])

    print(f"Seeds by family:")
    print(f"  Straw-only: N={len(straw_only_seeds)}  {sorted(straw_only_seeds)[:10]}...")
    print(f"  Pizza+Straw: N={len(pizza_straw_seeds)}  {sorted(pizza_straw_seeds)[:10]}...")

    t0 = time.time()

    # Run forensic on ALL straw-only seeds (worst regime)
    print(f"\nRunning forensic on {len(straw_only_seeds)} Straw-only seeds...")
    straw_results = run_group(straw_only_seeds, "Straw-only")

    # Run forensic on a sample of Pizza+Straw (comparison group)
    import random
    random.seed(42)
    pizza_sample = sorted(random.sample(pizza_straw_seeds, min(20, len(pizza_straw_seeds))))
    print(f"\nRunning forensic on {len(pizza_sample)} Pizza+Straw seeds (sample)...")
    pizza_results = run_group(pizza_sample, "Pizza+Straw (sample)")

    print(f"\nCompleted in {time.time()-t0:.0f}s")

    straw_analysis = analyze_group(straw_results, "STRAW-ONLY (V2 worst regime)")
    pizza_analysis = analyze_group(pizza_results, "PIZZA+STRAW (V2 best regime)")

    # Cross-regime comparison
    if straw_analysis and pizza_analysis:
        print(f"\n{'='*60}")
        print("CROSS-REGIME COMPARISON: Straw-only vs Pizza+Straw")
        print("(What's different when V2 struggles?)")
        print(f"{'='*60}")

        s_delta = straw_analysis["delta"]
        p_delta = pizza_analysis["delta"]

        comparison_keys = ["net_income", "implied_total_revenue", "explicit_costs",
                           "cost_land", "cost_feed", "total_hires",
                           "total_harvests", "total_fertilizes",
                           "plants_STRAWBERRY", "plants_WHEAT", "plants_MELON", "plants_CARROT"]

        print(f"\n  V2-minus-Dmitrii delta by regime (negative = Dmitrii advantage):")
        print(f"  {'Metric':30s}  {'Straw-only':>12s}  {'Pizza+Straw':>12s}  {'Diff':>10s}")
        print(f"  {'-'*68}")
        for k in comparison_keys:
            sv = s_delta.get(k, 0)
            pv = p_delta.get(k, 0)
            diff = sv - pv
            flag = " <<" if abs(diff) > 10 and sv < pv else ""
            print(f"  {k:30s}  {sv:>+12.1f}  {pv:>+12.1f}  {diff:>+10.1f}{flag}")

    # Save results
    output = {
        "straw_seeds": straw_only_seeds,
        "pizza_sample_seeds": pizza_sample,
        "straw_analysis": straw_analysis,
        "pizza_analysis": pizza_analysis,
    }

    def serialize(obj):
        if isinstance(obj, defaultdict):
            return dict(obj)
        return str(obj)

    with open(os.path.join(SCRATCH, "forensic_regime_analysis.json"), "w") as f:
        json.dump(output, f, default=serialize)

    print(f"\nResults saved to scratch/forensic_regime_analysis.json")
