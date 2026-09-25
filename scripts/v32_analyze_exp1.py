# SPDX-License-Identifier: MIT
"""V32 EXP-1 analysis: win matrix, pair stats, strategy fingerprints.

Usage: v32_analyze_exp1.py [--in results/v32_exp1.jsonl]
Writes V32_STRATEGY_FINGERPRINTS.json and prints the win matrix + pair table.
Pure analysis: reads executed legs only, runs no matches.
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v32_common import CORE_RR  # noqa: E402


def wash_sig(first_wash):
    """Canonical wash signature from first-wash market orders."""
    if not first_wash:
        return "none"
    parts = []
    for o in first_wash:
        if not o:
            continue
        parts.append("%s:%s:%s" % (o[0], o[1] if len(o) > 1 else "",
                                   o[2] if len(o) > 2 else ""))
    return "|".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default=os.path.join(REPO_ROOT, "results", "v32_exp1.jsonl"))
    args = ap.parse_args()
    recs = [json.loads(l) for l in open(args.inp) if l.strip()]

    # --- win matrix over CORE_RR (row beats column: wins-losses-ties, mean delta from row's view)
    mat = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, []]))
    durs = defaultdict(list)
    for r in recs:
        l, rr = r["left"], r["right"]
        d = r["delta"]
        w = "W" if d > 0 else ("L" if d < 0 else "T")
        mat[l][rr][0] += (w == "W")
        mat[l][rr][1] += (w == "L")
        mat[l][rr][2] += (w == "T")
        mat[l][rr][3].append(d)
        durs[(l, rr)].append(r["duration_sec"])

    experts = [e for e in CORE_RR if any(e in (r["left"], r["right"]) for r in recs)]
    print("legs=%d" % len(recs))
    print("pair W-L-T (row perspective) + mean delta:")
    hdr = "%-10s" % ""
    for e in experts:
        hdr += "%-22s" % e.replace("E", "").replace("_", "")[:20]
    print(hdr)
    for l in experts:
        row = "%-10s" % l.replace("E", "").replace("_", "")[:9]
        for r_ in experts:
            if l == r_:
                row += "%-22s" % "---"
                continue
            w, lo, t, ds = mat[l][r_]
            m = sum(ds) / len(ds) if ds else 0.0
            row += "%-22s" % ("%d-%d-%d m=%+.0f" % (w, lo, t, m))
        print(row)

    # --- totals per expert (all legs incl. parity/sanity, and core-only)
    print("\nper-expert totals (core RR only): W-L-T, mean delta, mean cash:")
    for e in experts:
        ds, cash = [], []
        w = lo = t = 0
        for r in recs:
            if r["left"] not in CORE_RR or r["right"] not in CORE_RR:
                continue
            if e == r["left"]:
                d = r["delta"]
                ds.append(d)
                cash.append(r["left_reward"])
            elif e == r["right"]:
                d = -r["delta"]
                ds.append(d)
                cash.append(r["right_reward"])
            else:
                continue
            w += d > 0
            lo += d < 0
            t += d == 0
        m = sum(ds) / len(ds) if ds else 0
        c = sum(cash) / len(cash) if cash else 0
        print("  %-10s %3d-%3d-%3d  mean_delta=%+8.0f  mean_cash=%8.0f  n=%d"
              % (e, w, lo, t, m, c, len(ds)))

    # --- parity + sanity
    print("\nparity (A7 vs AST, expect exact ties):")
    for r in recs:
        if {r["left"], r["right"]} == {"E2_A7", "E9_AST"}:
            print("  seed=%d %s delta=%+.0f digest_eq=%s"
                  % (r["seed"], r["winner"], r["delta"],
                     r["action_digest"] == r.get("action_digest")))
    print("sanity (V3 vs PASS):")
    for r in recs:
        if "E10_PASS" in (r["left"], r["right"]):
            v3 = r["left_reward"] if r["left"] == "E0_V3" else r["right_reward"]
            pa = r["right_reward"] if r["left"] == "E0_V3" else r["left_reward"]
            print("  seed=%d left=%s V3=%.0f PASS=%.0f winner=%s"
                  % (r["seed"], r["left"], v3, pa, r["winner"]))

    # --- timing
    all_durs = [r["duration_sec"] for r in recs]
    n_steps = recs[0]["telemetry"]["n_steps"]
    print("\nleg duration: n=%d mean=%.1fs p50=%.1fs max=%.1fs" % (
        len(all_durs), sum(all_durs) / len(all_durs),
        sorted(all_durs)[len(all_durs) // 2], max(all_durs)))
    print("env steps/leg=%d; single-worker agent-steps/s=%.0f"
          % (n_steps, 2 * n_steps / (sum(all_durs) / len(all_durs))))
    slow = sorted(durs.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:5]
    print("slowest pairs:", [(k, round(sum(v) / len(v), 1)) for k, v in slow])

    # --- fingerprints: aggregate telemetry per expert (as either seat)
    fps = {}
    for e in experts + ["E9_AST", "E10_PASS"]:
        legs = [r for r in recs if e in (r["left"], r["right"])]
        if not legs:
            continue
        agg = {"n_legs": len(legs), "wash": defaultdict(int),
               "hires": [], "fert": [], "collect": [], "cash": [],
               "sell_orders": [], "plant": defaultdict(int),
               "sell_qty": defaultdict(int)}
        for r in legs:
            s = 0 if r["left"] == e else 1
            t = r["telemetry"]
            agg["wash"][wash_sig(t["first_wash"][s])] += 1
            agg["hires"].append(t["hires"][s])
            agg["fert"].append(t["fertilize"][s])
            agg["collect"].append(t["collect"][s])
            agg["cash"].append(r["left_reward"] if s == 0 else r["right_reward"])
            mkt = t["mkt"][s]
            agg["sell_orders"].append(sum(v for k, v in mkt.items() if k.startswith("SELL/")))
            for k, v in t["plant"][s].items():
                agg["plant"][k] += v
            for k, v in t["sell_qty"][s].items():
                agg["sell_qty"][k] += v
        n = len(legs)
        fps[e] = {
            "n_legs": n,
            "wash_signature": dict(agg["wash"]),
            "hires_mean": round(sum(agg["hires"]) / n, 1),
            "fertilize_mean": round(sum(agg["fert"]) / n, 1),
            "collect_mean": round(sum(agg["collect"]) / n, 1),
            "cash_mean": round(sum(agg["cash"]) / n, 0),
            "sell_orders_mean": round(sum(agg["sell_orders"]) / n, 1),
            "plant_totals": dict(agg["plant"]),
            "sell_qty_totals": dict(agg["sell_qty"]),
        }
    out = {"created": "2026-09-22", "source": os.path.basename(args.inp),
           "n_legs": len(recs), "fingerprints": fps}
    with open(os.path.join(REPO_ROOT, "V32_STRATEGY_FINGERPRINTS.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("\nwrote V32_STRATEGY_FINGERPRINTS.json (%d experts)" % len(fps))


if __name__ == "__main__":
    main()
