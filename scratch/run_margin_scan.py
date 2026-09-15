"""
RAPID V2 vs DMITRII MARGIN SCAN — 150 seeds
Maps the full win/loss landscape to identify where and by how much
V2 loses to Dmitrii. Required before forensic decomposition.

Strategy: Run all 3 datasets (Discovery + Qual + Holdout) in parallel.
Output: per-seed margins, shop classification, distribution statistics.
"""

import sys, os, json, importlib.util, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")

def play_single(seed, v2_seat):
    """Play one game and return final cash for both agents."""
    import sys, os, importlib.util
    sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
    sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
    sys.path.insert(0, DMITRII_DIR)

    _spec = importlib.util.spec_from_file_location("dmitrii_agent", os.path.join(DMITRII_DIR, "main.py"))
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    dmitrii_fn = _mod.agent

    import kagsim
    from closed_loop_v2 import ClosedLoopAgentV2

    dm_seat = 1 - v2_seat
    g = kagsim.Game(seed)
    v2_agent = ClosedLoopAgentV2()

    while not g.done:
        obs_v2 = g.observe(v2_seat)
        obs_dm = g.observe(dm_seat)
        act_v2 = v2_agent.act(obs_v2)
        act_dm = dmitrii_fn(obs_dm)
        acts = [None, None]
        acts[v2_seat] = act_v2
        acts[dm_seat] = act_dm
        g.step(acts[0], acts[1])

    v2_cash = float(g.reward(v2_seat))
    dm_cash = float(g.reward(dm_seat))
    margin = v2_cash - dm_cash

    # Classify shop world from final obs
    obs_final = g.observe(v2_seat)
    shops = list(obs_final.get("town", {}).get("unlocked_shops", []))

    STRAW_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
    has_pizza = "PIZZA_SHOP" in shops
    has_straw = any(s in STRAW_SHOPS for s in shops)
    has_yarn = "YARN_SHOP" in shops

    if has_yarn and not has_pizza and not has_straw:
        shop_family = "Yarn"
    elif has_pizza and not has_straw:
        shop_family = "Pizza"
    elif has_straw and not has_pizza:
        shop_family = "Straw"
    elif has_pizza and has_straw:
        shop_family = "Pizza+Straw"
    elif has_yarn:
        shop_family = "Yarn+Other"
    else:
        shop_family = "None"

    return {
        "seed": seed, "v2_seat": v2_seat,
        "v2_cash": v2_cash, "dm_cash": dm_cash, "margin": margin,
        "shop_family": shop_family, "shops": shops,
    }


def run_scan(seeds, max_workers=8):
    """Run CRN paired scan: each seed played twice (v2=P0 and v2=P1)."""
    tasks = [(s, 0) for s in seeds] + [(s, 1) for s in seeds]
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(play_single, s, seat): (s, seat) for s, seat in tasks}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
            except Exception as e:
                s, seat = futures[fut]
                print(f"  ERROR seed={s} seat={seat}: {e}")

    return results


def print_summary(results, label):
    """Print summary statistics for a set of results."""
    # Pair up by seed
    by_seed = defaultdict(list)
    for r in results:
        by_seed[r["seed"]].append(r)

    combined_margins = []
    shop_margins = defaultdict(list)
    loss_details = []

    for seed, pair in sorted(by_seed.items()):
        if len(pair) == 2:
            cm = pair[0]["margin"] + pair[1]["margin"]
            combined_margins.append(cm)
            shop = pair[0]["shop_family"]
            shop_margins[shop].append(cm)
            if cm < -500:
                loss_details.append((cm, seed, shop))
        else:
            m = pair[0]["margin"]
            combined_margins.append(m * 2)
            shop_margins[pair[0]["shop_family"]].append(m * 2)

    n = len(combined_margins)
    mean_m = sum(combined_margins) / n
    sorted_m = sorted(combined_margins)
    median_m = sorted_m[n // 2]
    wins = sum(1 for m in combined_margins if m > 0)
    losses = sum(1 for m in combined_margins if m < 0)

    print(f"\n{'='*60}")
    print(f"{label} (N={n} seeds)")
    print(f"{'='*60}")
    print(f"  Win rate: {wins/n*100:.1f}%  Loss rate: {losses/n*100:.1f}%")
    print(f"  Mean combined margin: {mean_m:+.0f}")
    print(f"  Median combined margin: {median_m:+.0f}")
    print(f"  Worst loss: {sorted_m[0]:+.0f}  Best win: {sorted_m[-1]:+.0f}")
    print(f"  Large losses (<-1000): {sum(1 for m in combined_margins if m < -1000)}")
    print(f"  Large losses (<-5000): {sum(1 for m in combined_margins if m < -5000)}")

    print(f"\n  By shop family:")
    for fam, ms in sorted(shop_margins.items()):
        mean_f = sum(ms)/len(ms)
        wr = sum(1 for m in ms if m > 0) / len(ms)
        print(f"    {fam:15s}: N={len(ms):2d}  mean={mean_f:+.0f}  WR={wr*100:.0f}%")

    if loss_details:
        print(f"\n  Largest losses (seed, shop, combined_margin):")
        for m, s, shop in sorted(loss_details)[:15]:
            print(f"    seed {s:6d}  [{shop:12s}]  margin={m:+.0f}")

    return combined_margins, dict(by_seed)


if __name__ == "__main__":
    t0 = time.time()
    print("V2 vs DMITRII MARGIN SCAN — 150 seeds (50000-50149)")
    print("Running Discovery + Qualification + Fresh Holdout...")

    seeds = list(range(50000, 50150))
    results = run_scan(seeds, max_workers=8)

    # Split by dataset
    discovery = [r for r in results if 50000 <= r["seed"] <= 50049]
    qual = [r for r in results if 50050 <= r["seed"] <= 50099]
    holdout = [r for r in results if 50100 <= r["seed"] <= 50149]

    disc_margins, disc_by_seed = print_summary(discovery, "DISCOVERY (50000-50049)")
    qual_margins, qual_by_seed = print_summary(qual, "QUALIFICATION (50050-50099)")
    hold_margins, hold_by_seed = print_summary(holdout, "FRESH HOLDOUT (50100-50149)")

    all_margins = disc_margins + qual_margins + hold_margins
    mean_all = sum(all_margins) / len(all_margins)
    import math
    std_all = math.sqrt(sum((m - mean_all)**2 for m in all_margins) / (len(all_margins)-1))
    se_all = std_all / math.sqrt(len(all_margins))
    ci_lo = mean_all - 1.96 * se_all
    ci_hi = mean_all + 1.96 * se_all

    print(f"\n{'='*60}")
    print(f"OVERALL (N={len(all_margins)} seeds)")
    print(f"{'='*60}")
    print(f"  Mean: {mean_all:+.0f}  95% CI: [{ci_lo:+.0f}, {ci_hi:+.0f}]")
    print(f"  WR: {sum(1 for m in all_margins if m > 0)/len(all_margins)*100:.1f}%")
    print(f"  Time: {time.time()-t0:.0f}s")

    # Save full results
    out = {
        "discovery": [{k: v for k, v in r.items()} for r in discovery],
        "qualification": [{k: v for k, v in r.items()} for r in qual],
        "holdout": [{k: v for k, v in r.items()} for r in holdout],
        "disc_margins": disc_margins,
        "qual_margins": qual_margins,
        "hold_margins": hold_margins,
    }
    with open(os.path.join(BASE_DIR, "scratch", "v2_dmitrii_margin_scan.json"), "w") as f:
        json.dump(out, f)
    print("\nFull results saved to scratch/v2_dmitrii_margin_scan.json")
