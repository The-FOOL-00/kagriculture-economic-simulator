# SPDX-License-Identifier: MIT
"""V27 Phase 2: historical three-cohort stability analysis.

Reads results/v27_historical_matches.jsonl (120 paired V25-vs-V3 deltas).
Reports Objective A (terminal-cash delta) and Objective B (head-to-head
outcome) separately, with match-level AND seed-clustered inference
(seats within a seed are near-identical, so match-level SEs overstate
precision; the seed is the independent unit).

Outputs: results/v27_historical_stats.json + console summary.
"""

import json
import math
import os
import random
import statistics
import sys

import numpy as np
from scipy import stats as sstats

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IN_PATH = os.path.join(REPO_ROOT, "results", "v27_historical_matches.jsonl")
OUT_PATH = os.path.join(REPO_ROOT, "results", "v27_historical_stats.json")

RNG_SEED = 27
BOOT = 10000
TIE_MARGIN = 500.0  # V25's undocumented |delta|<=500 tie rule (sensitivity only)


def load():
    with open(IN_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def wlt(ds, tie_margin=0.0):
    w = sum(1 for d in ds if d > tie_margin)
    l = sum(1 for d in ds if d < -tie_margin)
    return (w, l, len(ds) - w - l)


def boot_ci(rng, vals, fn, n=BOOT):
    vals = np.asarray(vals, dtype=float)
    ests = np.empty(n)
    m = len(vals)
    for i in range(n):
        samp = vals[rng.integers(0, m, m)]
        ests[i] = fn(samp)
    return float(np.quantile(ests, 0.025)), float(np.quantile(ests, 0.975))


def seed_cluster_ci(rng, seed_groups, fn, n=BOOT):
    """Resample seeds (clusters), keep both seats; fn over pooled deltas."""
    ests = np.empty(n)
    m = len(seed_groups)
    for i in range(n):
        idx = rng.integers(0, m, m)
        pooled = np.concatenate([seed_groups[j] for j in idx])
        ests[i] = fn(pooled)
    return float(np.quantile(ests, 0.025)), float(np.quantile(ests, 0.975))


def main():
    recs = load()
    assert len(recs) == 120
    rng = np.random.default_rng(RNG_SEED)
    out = {"n_records": 120, "rng_seed": RNG_SEED, "boot_resamples": BOOT,
           "cohorts": {}, "seat_effect": {}, "cohort_heterogeneity": {},
           "data_quality": {}}

    # ---- data quality ----
    digests = [r["action_digest"] for r in recs]
    out["data_quality"]["unique_action_digests"] = len(set(digests))
    out["data_quality"]["duplicate_digests"] = len(digests) - len(set(digests))
    idle = [(r["cohort"], r["early_idle_rate"]) for r in recs
            if r["early_idle_rate"] is not None]
    for c in "AB":
        vs = [v for (cc, v) in idle if cc == c]
        out["data_quality"]["early_idle_rate_%s" % c] = {
            "n": len(vs), "mean": statistics.mean(vs),
            "min": min(vs), "max": max(vs)}

    # ---- per-cohort ----
    for cohort in "ABC":
        rs = [r for r in recs if r["cohort"] == cohort]
        ds = np.array([r["paired_delta"] for r in rs], dtype=float)
        seeds = sorted({r["seed"] for r in rs})
        groups = [np.array([r["paired_delta"] for r in rs if r["seed"] == s])
                  for s in seeds]
        seed_means = np.array([g.mean() for g in groups])
        w, l, t = wlt(ds)
        w500, l500, t500 = wlt(ds, TIE_MARGIN)
        wil = sstats.wilcoxon(ds, alternative="two-sided")
        sgn = sstats.binomtest(int(np.sum(ds > 0)), len(ds), 0.5,
                               alternative="two-sided")
        sgn_seed = sstats.binomtest(int(np.sum(seed_means > 0)), len(seed_means),
                                    0.5, alternative="two-sided")
        q = np.quantile(ds, [0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95])
        out["cohorts"][cohort] = {
            "n_matches": len(ds), "n_seeds": len(seeds),
            # Objective A: terminal-cash delta
            "A_mean": float(np.mean(ds)),
            "A_median": float(np.median(ds)),
            "A_sd": float(np.std(ds, ddof=1)),
            "A_se_match": float(np.std(ds, ddof=1) / math.sqrt(len(ds))),
            "A_se_seed": float(np.std(seed_means, ddof=1) / math.sqrt(len(seed_means))),
            "A_ci95_match_boot": list(boot_ci(rng, ds, np.mean)),
            "A_ci95_seed_boot": list(seed_cluster_ci(rng, groups, np.mean)),
            "A_ci95_median_seed_boot": list(seed_cluster_ci(rng, groups, np.median)),
            "A_min": float(ds.min()), "A_max": float(ds.max()),
            "A_q05": float(q[0]), "A_q10": float(q[1]),
            "A_q25": float(q[2]), "A_q75": float(q[4]),
            "A_q90": float(q[5]), "A_q95": float(q[6]),
            "A_iqr": float(q[4] - q[2]),
            "A_cv": (float(np.std(ds, ddof=1) / abs(np.mean(ds)))
                     if np.mean(ds) != 0 else None),
            "A_wilcoxon_W": float(wil.statistic), "A_wilcoxon_p": float(wil.pvalue),
            # Objective B: head-to-head outcome (exact-zero primary)
            "B_wlt_exact": [w, l, t],
            "B_positive_rate": float(np.mean(ds > 0)),
            "B_win_rate_all": float(w / len(ds)),
            "B_signtest_p": float(sgn.pvalue),
            "B_seed_positive_rate": float(np.mean(seed_means > 0)),
            "B_seed_signtest_p": float(sgn_seed.pvalue),
            # sensitivity: V25's undocumented |d|<=500 tie rule
            "B_wlt_margin500": [w500, l500, t500],
            "seed_means": [float(v) for v in seed_means],
        }

    # ---- seat effect ----
    for cohort in "ABC":
        rs = [r for r in recs if r["cohort"] == cohort]
        by_seed = {}
        for r in rs:
            by_seed.setdefault(r["seed"], {})[r["seat"]] = r["paired_delta"]
        diffs = np.array([v[0] - v[1] for v in by_seed.values()], dtype=float)
        exact = int(np.sum(diffs == 0))
        wil = sstats.wilcoxon(diffs[diffs != 0], alternative="two-sided") \
            if np.any(diffs != 0) else None
        s0 = np.array([v[0] for v in by_seed.values()])
        s1 = np.array([v[1] for v in by_seed.values()])
        corr = float(np.corrcoef(s0, s1)[0, 1]) if np.std(s0) > 0 and np.std(s1) > 0 else None
        out["seat_effect"][cohort] = {
            "n_seeds": len(by_seed), "seat_identical": exact,
            "seat_diff_mean": float(np.mean(diffs)),
            "seat_diff_maxabs": float(np.max(np.abs(diffs))),
            "seat_diff_ci95_boot": list(boot_ci(rng, diffs, np.mean)),
            "seat_wilcoxon_p": (float(wil.pvalue) if wil is not None else None),
            "seat0_seat1_corr": corr,
        }

    # ---- cohort heterogeneity ----
    ds = {c: np.array([r["paired_delta"] for r in recs if r["cohort"] == c])
          for c in "ABC"}
    gr = {c: [np.array([r["paired_delta"] for r in recs
                        if r["cohort"] == c and r["seed"] == s])
              for s in sorted({r["seed"] for r in recs if r["cohort"] == c})]
          for c in "ABC"}
    sm = {c: np.array([g.mean() for g in gr[c]]) for c in "ABC"}
    kw = sstats.kruskal(ds["A"], ds["B"], ds["C"])
    kw_seed = sstats.kruskal(sm["A"], sm["B"], sm["C"])
    out["cohort_heterogeneity"]["kruskal_match_p"] = float(kw.pvalue)
    out["cohort_heterogeneity"]["kruskal_seed_p"] = float(kw_seed.pvalue)
    # pairwise seed-level mean differences with cluster CIs
    pairs = {}
    for x, y in [("A", "B"), ("A", "C"), ("B", "C")]:
        diff = float(np.mean(sm[x]) - np.mean(sm[y]))
        ests = np.empty(BOOT)
        for i in range(BOOT):
            bx = np.concatenate([gr[x][j] for j in rng.integers(0, 20, 20)])
            by = np.concatenate([gr[y][j] for j in rng.integers(0, 20, 20)])
            ests[i] = bx.mean() - by.mean()
        # permutation test on seed means (labels shuffled)
        pooled = np.concatenate([sm[x], sm[y]])
        obs = abs(sm[x].mean() - sm[y].mean())
        cnt = 0
        for i in range(BOOT):
            perm = rng.permutation(pooled)
            if abs(perm[:20].mean() - perm[20:].mean()) >= obs:
                cnt += 1
        pairs["%s_minus_%s" % (x, y)] = {
            "seed_mean_diff": diff,
            "ci95_seed_boot": [float(np.quantile(ests, 0.025)),
                               float(np.quantile(ests, 0.975))],
            "permutation_p": cnt / BOOT,
        }
    out["cohort_heterogeneity"]["pairwise"] = pairs
    # variance comparison (Levene on seed means: do cohorts spread equally?)
    lev = sstats.levene(sm["A"], sm["B"], sm["C"])
    out["cohort_heterogeneity"]["levene_seed_p"] = float(lev.pvalue)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    # ---- console ----
    print("=== Objective A: paired terminal-cash delta (V25 - V3) ===")
    for c in "ABC":
        o = out["cohorts"][c]
        print("%s n=40/20seeds mean=%+9.2f med=%+8.1f sd=%8.2f "
              "seedCI=[%+8.1f,%+8.1f] min=%+7.0f max=%+7.0f wilcox_p=%.4g"
              % (c, o["A_mean"], o["A_median"], o["A_sd"],
                 o["A_ci95_seed_boot"][0], o["A_ci95_seed_boot"][1],
                 o["A_min"], o["A_max"], o["A_wilcoxon_p"]))
    print("=== Objective B: head-to-head (exact-zero W/L/T; margin500 in parens) ===")
    for c in "ABC":
        o = out["cohorts"][c]
        print("%s WLT=%dW/%dL/%dT (%dW/%dL/%dT) posrate=%.3f sign_p=%.4g "
              "seedpos=%.2f seedsign_p=%.4g"
              % (c, *o["B_wlt_exact"], *o["B_wlt_margin500"],
                 o["B_positive_rate"], o["B_signtest_p"],
                 o["B_seed_positive_rate"], o["B_seed_signtest_p"]))
    print("=== seat effect (seat0 - seat1 within seed) ===")
    for c in "ABC":
        o = out["seat_effect"][c]
        print("%s identical=%d/20 diffmean=%+.1f maxabs=%.0f corr=%s wilcox_p=%s"
              % (c, o["seat_identical"], o["seat_diff_mean"],
                 o["seat_diff_maxabs"], o["seat0_seat1_corr"], o["seat_wilcoxon_p"]))
    print("=== heterogeneity ===")
    h = out["cohort_heterogeneity"]
    print("kruskal match_p=%.4g seed_p=%.4g levene_seed_p=%.4g"
          % (h["kruskal_match_p"], h["kruskal_seed_p"], h["levene_seed_p"]))
    for k, v in h["pairwise"].items():
        print("%s diff=%+.1f CI=[%+.1f,%+.1f] perm_p=%.4g"
              % (k, v["seed_mean_diff"], *v["ci95_seed_boot"], v["permutation_p"]))
    print("data quality:", out["data_quality"])
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    sys.exit(main())
