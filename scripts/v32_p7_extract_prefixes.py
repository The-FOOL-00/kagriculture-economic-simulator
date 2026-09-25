# SPDX-License-Identifier: MIT
"""V32 P7 prefix dataset construction (Section 8).

Streams results/v32_p2_bc_legs.jsonl ONCE and extracts, for every recorded
seat, the exact expert prefixes H in {4, 8, 12, 24} via v32.p7.prefix (same
online-builder code path as P2/P3 training). Writes:

- results/v32_p7_prefixes.json : per-teacher canonical sequences, per-leg
  prefix signatures, opening-state summaries, consistency flags.

No live simulation, no relabeling, no holdout seeds (training legs only).
"""

import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p7.prefix import (PREFIX_HORIZONS, extract_prefix_steps,
                           farmer_sequence, hands_sequence, market_sequence)
from v32.p7.phase import phase_name
from v32.p2.dataset import load_legs

LEGS_PATH = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
OUT_PATH = os.path.join(REPO_ROOT, "results", "v32_p7_prefixes.json")


def sig(seq):
    return json.dumps(seq, sort_keys=False)


def main():
    per_teacher_farmer = {}
    per_teacher_market = {}
    per_teacher_hands = {}
    per_teacher_states = {}
    per_leg = []
    n_seats = 0
    for leg in load_legs(LEGS_PATH):
        for seat, (side, teacher) in enumerate(
                (("rows0", leg["left"]), ("rows1", leg["right"]))):
            rows = leg[side]
            n_seats += 1
            entry = {"key": leg["key"], "seed": leg["seed"], "seat": seat,
                     "teacher": teacher, "n_rows": len(rows)}
            for H in PREFIX_HORIZONS:
                steps = extract_prefix_steps(rows, teacher, leg["seed"], H)
                assert steps is not None, (leg["key"], seat, H)
                fseq = farmer_sequence(steps)
                mseq = market_sequence(steps)
                hseq = hands_sequence(steps)
                per_teacher_farmer.setdefault(teacher, {}).setdefault(
                    H, Counter())[sig(fseq)] += 1
                per_teacher_market.setdefault(teacher, {}).setdefault(
                    H, Counter())[sig(mseq)] += 1
                per_teacher_hands.setdefault(teacher, {}).setdefault(
                    H, Counter())[sig(hseq)] += 1
                if H == 24:
                    entry["p24_farmer"] = fseq
                    entry["p24_market"] = mseq
                    entry["p24_states"] = [
                        {"step": s["step"],
                         "farmer": s["ess"].get("farmer"),
                         "hands": len(s["ess"].get("hands", []) or []),
                         "money": s["ess"].get("money"),
                         "shed_cow": (s["ess"].get("shed", {}) or {}).get("COW", 0),
                         "shed_sheep": (s["ess"].get("shed", {}) or {}).get("SHEEP", 0),
                         "shed_wheat": (s["ess"].get("shed", {}) or {}).get("WHEAT", 0),
                         "inv0": (s["ess"].get("inv", []) or [{}])[0],
                         "seeds": s["ess"].get("seeds"),
                         "phase": phase_name(s["ess"])} for s in steps]
            per_teacher_states.setdefault(teacher, []).append(
                (leg["seed"], seat, entry["p24_states"]))
            per_leg.append(entry)

    teachers = sorted(per_teacher_farmer)
    summary = {"n_seats": n_seats, "teachers": teachers, "canonical": {},
               "market_variants": {}, "hands_variants": {}, "legs": per_leg}
    for t in teachers:
        summary["canonical"][t] = {}
        summary["market_variants"][t] = {}
        summary["hands_variants"][t] = {}
        for H in PREFIX_HORIZONS:
            fc = per_teacher_farmer[t][H]
            (top_f, top_n), = fc.most_common(1)
            summary["canonical"][t][str(H)] = {
                "n_variants": len(fc), "top_count": top_n,
                "top_seq": json.loads(top_f)}
            mc = per_teacher_market[t][H]
            summary["market_variants"][t][str(H)] = {
                "n_variants": len(mc),
                "top3": [{"count": n, "seq": json.loads(s)}
                         for s, n in mc.most_common(3)]}
            hc = per_teacher_hands[t][H]
            (top_h, top_hn), = hc.most_common(1)
            summary["hands_variants"][t][str(H)] = {
                "n_variants": len(hc), "top_count": top_hn,
                "top_seq": json.loads(top_h)}

    with open(OUT_PATH, "w") as f:
        json.dump(summary, f)
    print(f"seats={n_seats} teachers={teachers} -> {OUT_PATH}")
    for t in teachers:
        for H in PREFIX_HORIZONS:
            c = summary["canonical"][t][str(H)]
            print(f"{t} P{H}: farmer variants={c['n_variants']} "
                  f"top={c['top_count']}")
            if H == 4:
                for st, lit in c["top_seq"]:
                    print(f"    step {st}: {lit}")
        mv = summary["market_variants"][t]["4"]
        print(f"{t} P4: market variants={mv['n_variants']}")
        for v in mv["top3"][:2]:
            print(f"    count={v['count']}: {v['seq']}")


if __name__ == "__main__":
    main()
