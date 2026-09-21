# SPDX-License-Identifier: MIT
"""V27 Phase 1: build the normalized historical V25-vs-V3 dataset.

Reads the three vendored (verbatim, read-only) checkpoint files and emits
one normalized JSONL with a unified schema covering cohorts A/B/C:

  A = V25 discovery P3 arm, seeds 249430..249449 (40 records)
  B = V25 confirmation P3,   seeds 249450..249469 (40 records)
  C = V26 ARM1 standalone,    seeds 249470..249489 (40 records)

Each record is one mirrored match and already contains a paired delta
(V25 terminal cash minus V3 terminal cash, same game). Forensic checks:
seed ranges exact, 40 records/cohort, seats balanced, no duplicate
(cohort, seed, seat), and summary means reproduce the published values.
"""

import json
import os
import statistics
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_historical_matches.jsonl")

EXPECTED = {
    "A": {"range": (249430, 249449), "mean": 1300.70, "median": 1300.00,
          "wlt": (39, 0, 1)},
    "B": {"range": (249450, 249469), "mean": 453.77, "median": 424.50,
          "wlt": (14, 11, 15)},
    "C": {"range": (249470, 249489), "mean": -218.75, "median": -287.0,
          "wlt": None},  # W/L/T not published for V26 ARM1; report only
}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def norm(cohort, seed, seat, v25, v3, digest, idle, engine, code, source):
    delta = v25 - v3
    winner = "V25" if delta > 0 else ("V3" if delta < 0 else "TIE")
    return {
        "cohort": cohort,
        "seed": int(seed),
        "seat": int(seat),
        "pair_id": "%s:%d:%d" % (cohort, int(seed), int(seat)),
        "v25_reward": float(v25),
        "v3_reward": float(v3),
        "paired_delta": float(delta),
        "winner": winner,
        "action_digest": digest,
        "early_idle_rate": idle,
        "engine_version": engine,
        "code_hash": code,
        "source_file": source,
    }


def main():
    recs = []

    # Cohort A: V25 discovery, P3 arm only.
    for r in load(os.path.join(RESULTS, "v25_backbone_matches.jsonl")):
        if r["candidate"] != "V25_P3_UNIFIED":
            continue
        recs.append(norm("A", r["seed"], r["seat"], r["candidate_reward"],
                         r["baseline_reward"], r["action_digest"],
                         r.get("early_idle_rate"), r["engine_version"],
                         r["code_hash"], "v25_backbone_matches.jsonl"))

    # Cohort B: V25 confirmation (P3 only by construction).
    for r in load(os.path.join(RESULTS, "v25_confirmation_matches.jsonl")):
        assert r["candidate"] == "V25_P3_UNIFIED", r
        recs.append(norm("B", r["seed"], r["seat"], r["candidate_reward"],
                         r["baseline_reward"], r["action_digest"],
                         r.get("early_idle_rate"), r["engine_version"],
                         r["code_hash"], "v25_confirmation_matches.jsonl"))

    # Cohort C: V26 ARM1_V25_STANDALONE.
    for r in load(os.path.join(RESULTS, "v26_aec_transfer_matches.jsonl")):
        if r["arm"] != "ARM1_V25_STANDALONE":
            continue
        recs.append(norm("C", r["seed"], r["seat"], r["terminal_reward"],
                         r["opponent_reward"], r["action_digest"], None,
                         r["engine_version"], r["backbone_hash"],
                         "v26_aec_transfer_matches.jsonl"))

    # ---- forensic validation ----
    assert len(recs) == 120, len(recs)
    assert len({r["pair_id"] for r in recs}) == 120, "duplicate pair_id"
    by_cohort = {}
    for r in recs:
        by_cohort.setdefault(r["cohort"], []).append(r)

    print("cohort  n  seeds            seats  mean      median   W/L/T   idle?")
    for cohort in "ABC":
        rs = sorted(by_cohort[cohort], key=lambda r: (r["seed"], r["seat"]))
        assert len(rs) == 40, (cohort, len(rs))
        exp = EXPECTED[cohort]
        lo, hi = exp["range"]
        seeds = sorted({r["seed"] for r in rs})
        assert seeds == list(range(lo, hi + 1)), (cohort, seeds[:3], seeds[-3:])
        assert sorted(r["seat"] for r in rs) == [0] * 20 + [1] * 20, cohort
        ds = [r["paired_delta"] for r in rs]
        mean = statistics.mean(ds)
        median = statistics.median(ds)
        w = sum(1 for d in ds if d > 0)
        l = sum(1 for d in ds if d < 0)
        t = sum(1 for d in ds if d == 0)
        assert abs(mean - exp["mean"]) < 0.005, (cohort, mean, exp["mean"])
        assert abs(median - exp["median"]) < 0.005, (cohort, median)
        if exp["wlt"] is not None and (w, l, t) != exp["wlt"]:
            print("  !! FORENSIC FLAG %s: checkpoint W/L/T=%dW/%dL/%dT "
                  "differs from published %dW/%dL/%dT (data governs)"
                  % (cohort, w, l, t, *exp["wlt"]))
        idle = [r["early_idle_rate"] for r in rs if r["early_idle_rate"] is not None]
        print("  %s    40  %d..%d  20/20  %+8.2f  %+7.1f  %dW/%dL/%dT  %s"
              % (cohort, lo, hi, mean, median, w, l, t,
                 ("n=%d" % len(idle)) if idle else "n/a"))
        # code-hash anchor: every record must carry the frozen P3 digest
        hashes = {r["code_hash"] for r in rs}
        assert hashes == {"13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179"}, \
            (cohort, hashes)

    recs.sort(key=lambda r: (r["cohort"], r["seed"], r["seat"]))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote %s (%d records)" % (OUT_PATH, len(recs)))


if __name__ == "__main__":
    sys.exit(main())
