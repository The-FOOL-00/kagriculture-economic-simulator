"""
FORENSIC DISCOVERY RUN — 50 seeds, full economic telemetry
===========================================================
Runs 100 paired CRN matches (50 seeds × 2 seats) and saves
complete forensic records for all subsequent decomposition scripts.

Imports forensic_logger_v2.py for the core recording engine.
"""

import sys, os, json, time
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
DISCOVERY_SEEDS = list(range(50000, 50050))
MAX_WORKERS = 6
OUTPUT_FILE = os.path.join(BASE_DIR, "scratch", "forensic_discovery_raw.json")


def _worker(seed, v2_seat):
    """Subprocess worker — runs one forensic game."""
    import sys, os, importlib.util
    sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
    sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
    sys.path.insert(0, DMITRII_DIR)
    # Add scratch to path for forensic_logger_v2 import
    sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

    from forensic_logger_v2 import play_forensic_match
    return play_forensic_match(seed, v2_seat)


def run_forensic_discovery():
    t0 = time.time()
    print("=" * 80)
    print("FORENSIC DISCOVERY RUN — 50 seeds (50000-50049), CRN balanced")
    print(f"Workers: {MAX_WORKERS}  Total matches: {len(DISCOVERY_SEEDS) * 2}")
    print("=" * 80)

    tasks = [(s, 0) for s in DISCOVERY_SEEDS] + [(s, 1) for s in DISCOVERY_SEEDS]
    results = []
    errors = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futures = {exe.submit(_worker, s, seat): (s, seat) for s, seat in tasks}
        for i, fut in enumerate(as_completed(futures)):
            s, seat = futures[fut]
            try:
                r = fut.result()
                results.append(r)
                if (i + 1) % 10 == 0:
                    elapsed = time.time() - t0
                    pct = (i + 1) / len(tasks) * 100
                    eta = elapsed / (i + 1) * (len(tasks) - i - 1)
                    print(f"  {i+1:3d}/{len(tasks)} ({pct:.0f}%)  elapsed={elapsed:.0f}s  ETA={eta:.0f}s")
            except Exception as e:
                errors.append({"seed": s, "seat": seat, "error": str(e)})
                print(f"  ERROR seed={s} seat={seat}: {e}")

    print(f"\nCompleted {len(results)} matches in {time.time()-t0:.0f}s ({len(errors)} errors)")

    # Organize by seed
    from collections import defaultdict
    by_seed = defaultdict(list)
    for r in results:
        by_seed[r["seed"]].append(r)

    # Compute combined margins and quick summary
    combined = {}
    for seed, pair in sorted(by_seed.items()):
        if len(pair) == 2:
            p = {p_["v2_seat"]: p_ for p_ in pair}
            g0 = p.get(0, pair[0])
            g1 = p.get(1, pair[1])
            combined[seed] = {
                "seed": seed,
                "combined_margin": round(g0["paired_margin"] + g1["paired_margin"], 2),
                "v2_cash_g0": g0["v2_final_cash"],
                "dm_cash_g0": g0["dm_final_cash"],
                "v2_cash_g1": g1["v2_final_cash"],
                "dm_cash_g1": g1["dm_final_cash"],
                "shop_family": g0["shop_family"],
                "divergence_day": g0["divergence_day"],
                "gap_traj": g0["gap_trajectory_daily"],
            }

    # Print margin distribution
    margins = [v["combined_margin"] for v in combined.values()]
    margins_sorted = sorted(margins)
    n = len(margins)
    mean_m = sum(margins) / n if n else 0
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)

    print(f"\nMARGIN DISTRIBUTION (Discovery)")
    print(f"  N={n}  WR={wins/n*100:.1f}%  LR={losses/n*100:.1f}%")
    print(f"  Mean={mean_m:+.0f}  Median={margins_sorted[n//2]:+.0f}")
    print(f"  Worst={margins_sorted[0]:+.0f}  Best={margins_sorted[-1]:+.0f}")
    print(f"  < -1000: {sum(1 for m in margins if m < -1000)}")
    print(f"  < -5000: {sum(1 for m in margins if m < -5000)}")

    # Shop family breakdown
    from collections import Counter
    shop_counts = Counter(v["shop_family"] for v in combined.values())
    shop_margins = defaultdict(list)
    for v in combined.values():
        shop_margins[v["shop_family"]].append(v["combined_margin"])

    print(f"\n  By shop family:")
    for fam in sorted(shop_counts):
        ms = shop_margins[fam]
        mean_f = sum(ms)/len(ms)
        wr = sum(1 for m in ms if m > 0) / len(ms)
        print(f"    {fam:15s}: N={len(ms):2d}  mean={mean_f:+.0f}  WR={wr*100:.0f}%")

    # Largest losses
    loss_seeds = [(v["combined_margin"], v["seed"], v["shop_family"])
                  for v in combined.values() if v["combined_margin"] < -500]
    if loss_seeds:
        print(f"\n  Largest V2 losses:")
        for m, s, fam in sorted(loss_seeds)[:15]:
            print(f"    seed {s}  [{fam}]  combined_margin={m:+.0f}")

    # Save full raw data
    output = {
        "seeds": DISCOVERY_SEEDS,
        "combined_summary": combined,
        "raw_matches": results,
        "errors": errors,
    }

    # Serialize defaultdicts recursively
    def dedefault(obj):
        if isinstance(obj, defaultdict):
            return dict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, default=dedefault)

    print(f"\nFull forensic data saved to: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")
    return output


if __name__ == "__main__":
    run_forensic_discovery()
