# SPDX-License-Identifier: MIT
"""V28 Phases 8-9: lock raw results, emit paired CSV, compute six gates.

Reads results/v28_raw_results.jsonl (frozen tournament output).
Writes results/v28_paired_results.csv + results/v28_gate_stats.json.
Gate math EXACTLY per V28_PREREGISTRATION.md §§3-6 (frozen 91073c8).
"""

import csv
import hashlib
import json
import os
import statistics
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(REPO_ROOT, "results", "v28_raw_results.jsonl")
CSV = os.path.join(REPO_ROOT, "results", "v28_paired_results.csv")
STATS = os.path.join(REPO_ROOT, "results", "v28_gate_stats.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    recs = [json.loads(l) for l in open(RAW) if l.strip()]
    assert len(recs) == 80, len(recs)
    assert len({r["key"] for r in recs}) == 80, "duplicate keys!"
    seeds = sorted({r["seed"] for r in recs})
    assert seeds == list(range(249530, 249570)), seeds[:3]
    for r in recs:
        assert r["cand"] == "V27-ABL-A7" and r["base"] == "V3_STANDALONE"
        assert r["cand_digest"] == "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
        assert r["base_digest"] == "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
        assert r["engine_version"] == "1.32.7"
        assert r["cand_flags"] == {"call_v3_at_step0": True, "open_units": 30,
                                   "dispatch": False, "rewrite_step0_wash": True}
    rew = sum(1 for r in recs if r["step0_rewritten"])
    unexp = sum(1 for r in recs if r["step0_unexpected_shape"])
    pids = {r["pid"] for r in recs}
    nonces = {r["worker_nonce"] for r in recs}
    print("integrity: n=80 rewrite=%d/80 unexpected=%d pids=%d nonces=%d"
          % (rew, unexp, len(pids), len(nonces)))
    assert rew == 80 and unexp == 0

    ds = [r["delta"] for r in recs]
    mean = statistics.mean(ds)
    median = statistics.median(ds)
    sd = statistics.stdev(ds)
    w = sum(1 for d in ds if d > 0)
    l = sum(1 for d in ds if d < 0)
    t = sum(1 for d in ds if d == 0)
    posrate = w / len(ds)
    # Seed-clustered 95% CI (prereg §5 gate 5): t(0.975, df=39).
    by_seed = {}
    for r in recs:
        by_seed.setdefault(r["seed"], []).append(r["delta"])
    ms = [statistics.mean(v) for v in by_seed.values()]
    assert len(ms) == 40
    mse_mean = statistics.mean(ms)
    mse_sd = statistics.stdev(ms)
    se = mse_sd / (40 ** 0.5)
    try:
        from scipy.stats import t as tdist
        tcrit = float(tdist.ppf(0.975, 39))
    except ImportError:
        tcrit = 2.0227  # t(0.975, df=39)
    ci_lo, ci_hi = mse_mean - tcrit * se, mse_mean + tcrit * se
    seed_pos = sum(1 for m in ms if m > 0)
    mn, mx = min(ds), max(ds)
    qs = statistics.quantiles(ds, n=100)
    q05, q95 = qs[4], qs[94]
    # Seats
    s0 = [r["delta"] for r in recs if r["seat"] == 0]
    s1 = [r["delta"] for r in recs if r["seat"] == 1]
    seat_diff = [by_seed[s][0] - by_seed[s][1] for s in by_seed]
    # Concentration (diagnostic)
    tot = sum(ds)
    contrib = sorted(((abs(sum(v)), s) for s, v in by_seed.items()), reverse=True)
    top1_share = contrib[0][0] / abs(tot)
    top3_share = sum(c[0] for c in contrib[:3]) / abs(tot)
    no_max = (tot - mx) / (len(ds) - 1)
    no_min = (tot - mn) / (len(ds) - 1)
    trimmed = statistics.mean(sorted(ds)[4:-4])  # 5% trimmed each side
    # Secondary: bootstrap CI of mean (seeded RNG, labeled secondary)
    import random
    rng = random.Random(28)
    boots = []
    for _ in range(10000):
        samp = [rng.choice(ms) for _ in range(40)]
        boots.append(statistics.mean(samp))
    boots.sort()
    boot_ci = [boots[250], boots[9749]]
    # Wilcoxon (secondary)
    try:
        from scipy.stats import wilcoxon
        wil_p = float(wilcoxon(ds).pvalue)
    except ImportError:
        wil_p = None

    gates = {
        "gate1_mean_gt_0": {"value": mean, "pass": mean > 0},
        "gate2_median_gt_0": {"value": median, "pass": median > 0},
        "gate3_posrate_gt_50": {"value": posrate, "wins": w, "n": 80,
                                "pass": posrate > 0.50},
        "gate4_wins_gt_losses": {"wins": w, "losses": l, "ties": t,
                                 "pass": w > l},
        "gate5_seed_ci_positive": {"ci": [ci_lo, ci_hi], "tcrit": tcrit,
                                   "seed_mean": mse_mean, "seed_sd": mse_sd,
                                   "pass": ci_lo > 0},
        "gate6_tail_floor": {"min": mn, "pass": mn > -10000},
    }
    stats = {
        "n_matches": 80, "n_seeds": 40, "mean": mean, "median": median,
        "sd": sd, "se_match": sd / (80 ** 0.5), "min": mn, "max": mx,
        "q05": q05, "q95": q95, "wlt_exact": [w, l, t],
        "posrate_match": posrate, "seed_pos_rate": seed_pos / 40,
        "seed_pos_count": seed_pos, "seed_ci95": [ci_lo, ci_hi],
        "seed_mean": mse_mean, "seed_sd": mse_sd,
        "seat0_mean": statistics.mean(s0), "seat1_mean": statistics.mean(s1),
        "seat0_median": statistics.median(s0),
        "seat1_median": statistics.median(s1),
        "seat_diff_max_abs": max(abs(d) for d in seat_diff),
        "seat_identical": sum(1 for d in seat_diff if d == 0),
        "top1_seed_share": top1_share, "top3_seed_share": top3_share,
        "top_contributors": [(s, c) for c, s in contrib[:5]],
        "mean_excl_max": no_max, "mean_excl_min": no_min,
        "trimmed_mean_5pct": trimmed,
        "bootstrap_ci95_secondary": boot_ci, "wilcoxon_p_secondary": wil_p,
        "gates": gates, "all_gates_pass": all(g["pass"] for g in gates.values()),
        "raw_sha256": sha256_file(RAW),
    }
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["seed", "seat", "a7_reward", "v3_reward", "delta",
                     "winner", "action_digest", "money_digest",
                     "step0_rewritten", "pid", "mode"])
        for r in sorted(recs, key=lambda r: (r["seed"], r["seat"])):
            wr.writerow([r["seed"], r["seat"], r["cand_reward"],
                         r["base_reward"], r["delta"], r["winner"],
                         r["action_digest"], r["money_digest"],
                         r["step0_rewritten"], r["pid"], r["mode"]])
    stats["csv_sha256"] = sha256_file(CSV)
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    print(json.dumps({k: v for k, v in stats.items()
                      if k not in ("gates", "top_contributors")}, indent=1))
    print("GATES:", {k: (v["pass"], v.get("value", v.get("ci", v.get("min"))))
                     for k, v in gates.items()})
    print("top contributors:", stats["top_contributors"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
