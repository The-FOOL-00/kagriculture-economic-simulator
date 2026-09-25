# SPDX-License-Identifier: MIT
"""V32 P1 forensics: expert x opponent payoff/regret analysis over EXP-1 legs.

Pure analysis: reads results/v32_exp1.jsonl only, runs no matches.
Writes V32_P1_FORENSICS.json and prints matrices for V32_P1_FORENSICS.md.

Framing: each EXP-1 leg L-vs-R on seed s yields TWO directed rows:
  (seed s, opponent R) -> cash of L ; (seed s, opponent L) -> cash of R.
Router rows are (seed, opponent) with a cash/W-L vector over router classes.
"""

import json
import math
import os
import sys
from collections import defaultdict
from itertools import combinations

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from v32_common import CORE_RR  # noqa: E402

ROUTER_CLASSES = ["E0_V3", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015"]
SHORT = {"E0_V3": "V3", "E1_V22R1": "V22R1", "E2_A7": "A7",
         "E3_V25P3": "V25P3", "E4_A1": "A1", "E5_A2": "A2",
         "E6_W72": "W72", "E7_W2015": "W2015", "E8_DMITRII": "DMIT"}


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    inp = os.path.join(REPO_ROOT, "results", "v32_exp1.jsonl")
    recs = [json.loads(l) for l in open(inp) if l.strip()]
    core = [r for r in recs
            if r["left"] in CORE_RR and r["right"] in CORE_RR]
    print("legs total=%d core=%d" % (len(recs), len(core)))

    # --- quarantine re-verification: no CONFIRM / protected seed in records
    bad = [r["seed"] for r in recs
           if (249695 <= r["seed"] <= 249734)
           or (214200 <= r["seed"] <= 214249)
           or (340090 <= r["seed"] <= 340199)]
    assert not bad, bad[:5]
    seeds = sorted({r["seed"] for r in core})
    print("seeds=%s n=%d (all inside V32-EXP1 block)" % (seeds, len(seeds)))

    # --- directed rows: (seed, opponent) -> {expert: [cash...]}
    rows = defaultdict(lambda: defaultdict(list))   # (seed,opp)[exp] = [cash]
    wrows = defaultdict(lambda: defaultdict(list))  # (seed,opp)[exp] = [win?]
    for r in core:
        s = r["seed"]
        rows[(s, r["right"])][r["left"]].append(r["left_reward"])
        rows[(s, r["left"])][r["right"]].append(r["right_reward"])
        wrows[(s, r["right"])][r["left"]].append(1.0 if r["delta"] > 0 else
                                                (0.0 if r["delta"] < 0 else 0.5))
        wrows[(s, r["left"])][r["right"]].append(1.0 if r["delta"] < 0 else
                                                (0.0 if r["delta"] > 0 else 0.5))

    # --- 1. expert x opponent CASH matrix (mean over seeds x seats)
    cash_m = defaultdict(lambda: defaultdict(list))
    wl_m = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for (s, opp), d in sorted(rows.items()):
        for exp, cs in d.items():
            cash_m[exp][opp].extend(cs)
    for (s, opp), d in sorted(wrows.items()):
        for exp, ws in d.items():
            for w in ws:
                wl_m[exp][opp][0 if w == 1.0 else (1 if w == 0.0 else 2)] += 1

    print("\n== expert x opponent MEAN CASH (row expert vs column opponent) ==")
    hdr = "%-7s" % ""
    for o in CORE_RR:
        hdr += "%9s" % SHORT[o]
    print(hdr)
    for e in CORE_RR:
        row = "%-7s" % SHORT[e]
        for o in CORE_RR:
            row += "%9s" % ("---" if e == o else
                             "%d" % round(mean(cash_m[e][o])))
        print(row)

    print("\n== expert x opponent W-L-T (row expert vs column opponent) ==")
    print(hdr)
    for e in CORE_RR:
        row = "%-7s" % SHORT[e]
        for o in CORE_RR:
            w, l, t = wl_m[e][o]
            row += "%9s" % ("---" if e == o else "%d-%d-%d" % (w, l, t))
        print(row)

    # --- 2. per (seed, opponent): best expert by cash and by W/L
    or_cash_gap, or_wl_gap = [], []   # oracle minus fixed-A7, per row
    or_cash_gap_w72, fixed_rows = [], []
    best_by_opp_cash = defaultdict(lambda: defaultdict(int))
    best_by_opp_wl = defaultdict(lambda: defaultdict(int))
    best_by_seed_cash = defaultdict(lambda: defaultdict(int))
    per_row = []
    for (s, opp), d in sorted(rows.items()):
        if opp not in ROUTER_CLASSES and opp != "E1_V22R1" and opp not in (
                "E4_A1", "E5_A2", "E8_DMITRII"):
            continue
        # cash values averaged over the 2 mirrored seats for this (seed,opp,exp)
        cavg = {e: mean(cs) for e, cs in d.items() if e in ROUTER_CLASSES}
        wavg = {e: mean(wrows[(s, opp)][e]) for e in cavg}
        if "E2_A7" not in cavg:
            continue
        a7 = cavg["E2_A7"]
        w72 = cavg.get("E6_W72")
        best_cash = max(cavg, key=lambda e: cavg[e])
        # best by W/L: highest win score, tie-break by cash
        best_wl = max(cavg, key=lambda e: (wavg[e], cavg[e]))
        or_cash_gap.append(cavg[best_cash] - a7)
        or_wl_gap.append(wavg[best_wl] - wavg["E2_A7"])
        if w72 is not None:
            or_cash_gap_w72.append(cavg[best_cash] - w72)
        best_by_opp_cash[opp][best_cash] += 1
        best_by_opp_wl[opp][best_wl] += 1
        best_by_seed_cash[s][best_cash] += 1
        fixed_rows.append({"seed": s, "opp": opp,
                           "cash": {SHORT[e]: round(v) for e, v in cavg.items()},
                           "best_cash": SHORT[best_cash],
                           "best_wl": SHORT[best_wl],
                           "a7_cash": round(a7),
                           "oracle_cash": round(cavg[best_cash])})
        per_row.append(((s, opp), cavg, wavg))

    print("\n== oracle-vs-fixed gaps over %d (seed,opponent) rows ==" % len(or_cash_gap))
    print("oracle-cash minus A7: mean=%+.0f median=%+.0f max=%+.0f n_pos=%d/%d"
          % (mean(or_cash_gap), sorted(or_cash_gap)[len(or_cash_gap) // 2],
             max(or_cash_gap), sum(1 for x in or_cash_gap if x > 0), len(or_cash_gap)))
    print("oracle-cash minus W72: mean=%+.0f median=%+.0f n_pos=%d/%d"
          % (mean(or_cash_gap_w72), sorted(or_cash_gap_w72)[len(or_cash_gap_w72) // 2],
             sum(1 for x in or_cash_gap_w72 if x > 0), len(or_cash_gap_w72)))
    print("oracle-W/L minus A7-W/L (win-score): mean=%+.3f n_pos=%d/%d"
          % (mean(or_wl_gap), sum(1 for x in or_wl_gap if x > 0), len(or_wl_gap)))

    print("\n== best-expert-by-CASH counts per opponent (rows=seeds) ==")
    for opp in CORE_RR:
        if opp in best_by_opp_cash:
            print("  vs %-7s %s" % (SHORT[opp], dict(
                (SHORT[e], c) for e, c in best_by_opp_cash[opp].items())))
    print("== best-expert-by-CASH counts per seed (rows=opponents) ==")
    for s in seeds:
        print("  seed %d %s" % (s, dict(
            (SHORT[e], c) for e, c in best_by_seed_cash[s].items())))
    print("== best-expert-by-W/L counts per opponent ==")
    for opp in CORE_RR:
        if opp in best_by_opp_wl:
            print("  vs %-7s %s" % (SHORT[opp], dict(
                (SHORT[e], c) for e, c in best_by_opp_wl[opp].items())))

    # --- 3. regret of fixed experts vs oracle-cash (per row)
    print("\n== fixed-expert REGRET vs oracle-cash (mean over rows) ==")
    regrets = {}
    for e in ROUTER_CLASSES:
        rs = [max(cavg.values()) - cavg[e] for (_, cavg, _) in
              [(k, c, w) for (k, c, w) in per_row if e in c]]
        regrets[e] = rs
        print("  %-7s mean=%7.0f median=%7.0f p90=%7.0f max=%7.0f n=%d"
              % (SHORT[e], mean(rs), sorted(rs)[len(rs) // 2],
                 sorted(rs)[int(len(rs) * 0.9)], max(rs), len(rs)))

    # --- 4. opponent-is-economy: per (seed, expert) cash spread across opponents
    print("\n== per (seed,expert) cash spread across opponents ==")
    spreads = []
    per_exp_seed = defaultdict(lambda: defaultdict(list))
    for (s, opp), d in rows.items():
        for e, cs in d.items():
            if e in ROUTER_CLASSES:
                per_exp_seed[e][s].append(mean(cs))
    for e in ROUTER_CLASSES:
        for s in seeds:
            vs = per_exp_seed[e][s]
            if len(vs) > 1:
                spreads.append((max(vs) - min(vs), e, s))
    spreads.sort(reverse=True)
    for sp, e, s in spreads[:8]:
        print("  %-7s seed=%d spread=%d" % (SHORT[e], s, round(sp)))
    print("  median spread=%d n=%d" % (
        round(sorted(x[0] for x in spreads)[len(spreads) // 2]), len(spreads)))

    # --- 5. CROSS vs WITHIN pair-cash (post-hoc G1/G2, descriptive n=6)
    G1 = {"E0_V3", "E1_V22R1", "E4_A1", "E5_A2"}
    G2 = {"E2_A7", "E3_V25P3", "E7_W2015"}
    print("\n== CROSS vs WITHIN pair-cash per seed (post-hoc, descriptive) ==")
    cross_within = {}
    for s in seeds:
        cr, wi = [], []
        for r in core:
            if r["seed"] != s:
                continue
            pair = r["left_reward"] + r["right_reward"]
            a, b = r["left"], r["right"]
            if (a in G1) != (b in G1) and a in G1 | G2 and b in G1 | G2:
                cr.append(pair)
            elif a in G1 | G2 and b in G1 | G2 and (
                    (a in G1 and b in G1) or (a in G2 and b in G2)):
                wi.append(pair)
        cross_within[s] = {"cross": round(mean(cr)), "within": round(mean(wi)),
                           "gap": round(mean(cr) - mean(wi))}
        print("  seed=%d CROSS=%d WITHIN=%d gap=%+d" % (
            s, mean(cr), mean(wi), mean(cr) - mean(wi)))

    # --- 6. W72 decoupling: wins vs own cash
    print("\n== W/L-cash decoupling check (core RR) ==")
    for e in ROUTER_CLASSES:
        w = l = t = 0
        cash = []
        for r in core:
            if e == r["left"]:
                d = r["delta"]
                cash.append(r["left_reward"])
            elif e == r["right"]:
                d = -r["delta"]
                cash.append(r["right_reward"])
            else:
                continue
            w += d > 0
            l += d < 0
            t += d == 0
        print("  %-7s W-L-T=%d-%d-%d winrate=%.3f mean_cash=%d" % (
            SHORT[e], w, l, t, w / (w + l + t), mean(cash)))

    # --- 7. seat symmetry re-verification
    asym = 0
    for r in core:
        mir = [x for x in core if x["left"] == r["right"]
               and x["right"] == r["left"] and x["seed"] == r["seed"]]
        if mir:
            m = mir[0]
            if not (m["left_reward"] == r["right_reward"]
                    and m["right_reward"] == r["left_reward"]):
                asym += 1
    print("\nseat-asymmetric mirror pairs: %d (expect 0)" % asym)

    # --- 8. wash-ladder margins (mechanism table)
    print("\n== wash-ladder pairwise margins (row minus column, mean $) ==")
    ladder = ["E6_W72", "E7_W2015", "E2_A7", "E0_V3"]
    hdr = "%-7s" % ""
    for o in ladder:
        hdr += "%9s" % SHORT[o]
    print(hdr)
    for e in ladder:
        row = "%-7s" % SHORT[e]
        for o in ladder:
            if e == o:
                row += "%9s" % "---"
                continue
            ds = []
            for r in core:
                if {r["left"], r["right"]} == {e, o}:
                    ds.append(r["delta"] if r["left"] == e else -r["delta"])
            row += "%9s" % ("%+.0f" % mean(ds))
        print(row)

    out = {
        "source": "results/v32_exp1.jsonl",
        "n_legs_core": len(core),
        "seeds": seeds,
        "router_classes": ROUTER_CLASSES,
        "cash_matrix": {e: {o: round(mean(cash_m[e][o])) for o in CORE_RR if e != o}
                        for e in CORE_RR},
        "wl_matrix": {e: {o: wl_m[e][o] for o in CORE_RR if e != o}
                      for e in CORE_RR},
        "oracle_cash_minus_a7": [round(x) for x in or_cash_gap],
        "oracle_cash_minus_w72": [round(x) for x in or_cash_gap_w72],
        "fixed_regret_vs_oracle_cash": {e: [round(x) for x in regrets[e]]
                                        for e in regrets},
        "best_cash_by_opp": {o: {e: c for e, c in d.items()}
                             for o, d in best_by_opp_cash.items()},
        "best_wl_by_opp": {o: {e: c for e, c in d.items()}
                           for o, d in best_by_opp_wl.items()},
        "cross_within_posthoc": cross_within,
        "seat_asymmetric_mirrors": asym,
        "per_row": fixed_rows,
    }
    with open(os.path.join(REPO_ROOT, "V32_P1_FORENSICS.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("\nwrote V32_P1_FORENSICS.json")


if __name__ == "__main__":
    main()
