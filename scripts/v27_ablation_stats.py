# SPDX-License-Identifier: MIT
"""V27 Phase 8 readout: ablation statistics (exploratory, consumed seeds).

Reads results/v27_ablation_matches.jsonl + the P3-vs-V3 ledger baseline.
Emits results/v27_ablation_stats.json + console full table (§29: complete
table, no cherry-pick).
"""

import json
import math
import os
import statistics
import sys

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(REPO_ROOT, "results")
IN_PATH = os.path.join(RESULTS, "v27_ablation_matches.jsonl")
OUT_PATH = os.path.join(RESULTS, "v27_ablation_stats.json")


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def seed_ci(seed_means, n_boot=10000, seed=27):
    rng = np.random.default_rng(seed)
    v = np.asarray(seed_means, dtype=float)
    m = len(v)
    ests = np.sort([rng.choice(v, m, replace=True).mean() for _ in range(n_boot)])
    return [float(ests[250]), float(ests[9750])]


def main():
    recs = load(IN_PATH)
    led = [json.loads(l) for l in open(os.path.join(RESULTS, "v27_ledger.jsonl"))
           if l.strip()]
    p3d = {}
    for x in led:
        if x["series"] in ("DISC-P3'", "CONF-P3'", "V26A1"):
            p3d[(x["seed"], x["seat"])] = x["terminal_delta"]
    out = {"configs": {}, "paired_vs_p3": {}, "square": {}}
    cfgs = sorted({r["config"] for r in recs})
    for c in cfgs:
        rows = [r for r in recs if r["config"] == c]
        ds = [r["delta"] for r in rows]
        by_seed = {}
        for r in rows:
            by_seed.setdefault(r["seed"], []).append(r["delta"])
        sm = [statistics.mean(v) for v in by_seed.values()]
        w = sum(1 for d in ds if d > 0)
        l = sum(1 for d in ds if d < 0)
        out["configs"][c] = {
            "n": len(ds), "n_seeds": len(by_seed),
            "mean": statistics.mean(ds), "median": statistics.median(ds),
            "sd": statistics.stdev(ds),
            "se_seed": statistics.stdev(sm) / math.sqrt(len(sm)),
            "ci95_seed": seed_ci(sm),
            "wlt": [w, l, len(ds) - w - l],
            "min": min(ds), "max": max(ds),
            "seed_pos_rate": sum(1 for v in sm if v > 0) / len(sm),
        }
    # paired variant-minus-P3 via common V3 baseline (same seed/seat)
    for v in ("V27-ABL-A1", "V27-ABL-A2", "V27-ABL-A3", "V27-ABL-V3S", "V27-ABL-A7"):
        rows = [r for r in recs if r["config"] == "%s-vs-V3" % v]
        if not rows:
            continue
        diffs = [r["delta"] - p3d[(r["seed"], r["seat"])] for r in rows]
        by_seed = {}
        for r, d in zip(rows, diffs):
            by_seed.setdefault(r["seed"], []).append(d)
        sm = [statistics.mean(vv) for vv in by_seed.values()]
        out["paired_vs_p3"][v] = {
            "n": len(diffs), "mean": statistics.mean(diffs),
            "median": statistics.median(diffs), "sd": statistics.stdev(diffs),
            "se_seed": statistics.stdev(sm) / math.sqrt(len(sm)),
            "ci95_seed": seed_ci(sm),
        }
    # qty x call/bypass square (vs-V3 means)
    sq = {}
    for v in ("V27-ABL-A1", "V27-ABL-A2", "V27-ABL-A3", "V27-ABL-V3S", "V27-ABL-A7"):
        k = "%s-vs-V3" % v
        if k in out["configs"]:
            sq[v] = out["configs"][k]["mean"]
    sq["P3-vs-V3"] = statistics.mean(p3d.values())
    out["square"] = sq
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    for c in cfgs:
        o = out["configs"][c]
        print("%-18s n=%d mean=%+9.1f med=%+8.1f sd=%7.1f seedCI=[%+8.1f,%+8.1f] %dW/%dL/%dT" % (
            c, o["n"], o["mean"], o["median"], o["sd"], o["ci95_seed"][0],
            o["ci95_seed"][1], *o["wlt"]))
    print("--- paired variant-minus-P3 (common V3 baseline) ---")
    for v, o in out["paired_vs_p3"].items():
        print("%s: mean=%+9.1f med=%+8.1f sd=%7.1f seedCI=[%+8.1f,%+8.1f]" % (
            v, o["mean"], o["median"], o["sd"], o["ci95_seed"][0], o["ci95_seed"][1]))
    print("square:", {k: round(v, 1) for k, v in sq.items()})
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    sys.exit(main())
