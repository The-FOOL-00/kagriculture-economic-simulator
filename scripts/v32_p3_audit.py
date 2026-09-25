# SPDX-License-Identifier: MIT
"""V32 P3 dataset audit: P2 BC legs -> P3 factorized label statistics.

One pass over results/v32_p2_bc_legs.jsonl. Writes results/v32_p3_audit.json
(machine-readable) and prints a text summary for V32_P3_DATASET_AUDIT.md.
No torch dependency. Read-only on data; no matches executed.
"""

import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p3 import codec as C  # noqa: E402

LEGS = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
OUT = os.path.join(REPO_ROOT, "results", "v32_p3_audit.json")
VAL_SEEDS = {249647, 249648, 249649}


def sha16(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main():
    u_op = Counter()
    u_arg = Counter()
    u_qty = Counter()
    m_op = Counter()
    m_item = Counter()
    m_qty = Counter()
    hand_n = Counter()
    mkt_n = Counter()
    farmer_op = Counter()
    per_slot_mop = [Counter() for _ in range(C.M_MARKET_SLOTS)]
    n_steps = n_legs = 0
    n1 = n2 = n3 = utr = mtr = 0
    none_farmer = none_hands = none_mkt = 0
    step0 = []  # (seed, side, teacher, market lite, wash_bool)
    teachers = Counter()
    seeds = set()
    train_steps = val_steps = 0
    plant_zero_seed = 0  # PLANT_c emitted while seeds[c]==0 (provably-noop)

    for line in open(LEGS):
        leg = json.loads(line)
        n_legs += 1
        seeds.add(leg["seed"])
        for side, teacher in (("rows0", leg["left"]), ("rows1", leg["right"])):
            teachers[teacher] += len(leg[side])
            for row in leg[side]:
                n_steps += 1
                if leg["seed"] in VAL_SEEDS:
                    val_steps += 1
                else:
                    train_steps += 1
                ess, act = row["e"], row["a"] or {}
                n_h = len(ess.get("hands", []) or [])
                hand_n[n_h] += 1
                mkt = act.get("market") or []
                mkt_n[len(mkt)] += 1
                if act.get("farmer") is None:
                    none_farmer += 1
                if act.get("hands") is None:
                    none_hands += 1
                if act.get("market") is None:
                    none_mkt += 1
                enc = C.encode_action(act, n_h)
                for f in enc["flags"]:
                    if f.endswith("N1"):
                        n1 += 1
                    elif f.endswith("N2"):
                        n2 += 1
                    elif f.endswith("N3"):
                        n3 += 1
                    elif f == "U:TRUNC":
                        utr += 1
                    elif f == "M:TRUNC":
                        mtr += 1
                for j, (o, a, q) in enumerate(enc["u"]):
                    u_op[C.U_OP[o]] += 1
                    if C.U_OP[o] in ("PLANT", "PICKUP", "PLACE"):
                        u_arg[C.U_ARG[a]] += 1
                    if C.U_OP[o] in ("PICKUP", "PLACE"):
                        u_qty[str(C.U_QTY[q])] += 1
                    if j == 0:
                        farmer_op[C.U_OP[o]] += 1
                    if C.U_OP[o] == "PLANT" and C.plant_crop_masked(
                            ess.get("seeds", {}), C.U_ARG[a]):
                        plant_zero_seed += 1
                for s, (o, i, q) in enumerate(enc["m"]):
                    m_op[C.M_OP[o]] += 1
                    per_slot_mop[s][C.M_OP[o]] += 1
                    if C.M_OP[o] in C.M_QTY_OPS:
                        m_item[C.M_ITEM[i]] += 1
                        m_qty[str(C.M_QTY[q])] += 1
                if ess.get("step") == 0:
                    ops = [o[0] for o in mkt if isinstance(o, list) and o]
                    wash = (any(o in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL")
                                for o in ops) and "SELL" in ops)
                    step0.append({"seed": leg["seed"], "side": side,
                                  "teacher": teacher, "wash": wash,
                                  "market": mkt if wash else None})

    wash_by_teacher = Counter()
    tot_by_teacher = Counter()
    for r in step0:
        tot_by_teacher[r["teacher"]] += 1
        if r["wash"]:
            wash_by_teacher[r["teacher"]] += 1

    res = {
        "legs": n_legs, "steps": n_steps, "train_steps": train_steps,
        "val_steps": val_steps, "seeds": sorted(seeds),
        "val_seeds": sorted(VAL_SEEDS), "teachers": dict(teachers),
        "legs_sha16": sha16(LEGS),
        "vocab_sha16": sha16(os.path.join(REPO_ROOT,
                                           "results", "v32_p2_vocab.json")),
        "U_OP": dict(u_op), "U_ARG_cond": dict(u_arg),
        "U_QTY_cond": dict(u_qty), "M_OP": dict(m_op),
        "M_ITEM_cond": dict(m_item), "M_QTY_cond": dict(m_qty),
        "farmer_OP": dict(farmer_op),
        "per_slot_M_OP": [dict(c) for c in per_slot_mop],
        "hand_count": {str(k): v for k, v in sorted(hand_n.items())},
        "market_count": {str(k): v for k, v in sorted(mkt_n.items())},
        "max_hands": max(hand_n), "max_market": max(mkt_n),
        "N1": n1, "N2": n2, "N3": n3, "U_TRUNC": utr, "M_TRUNC": mtr,
        "none_farmer": none_farmer, "none_hands": none_hands,
        "none_market": none_mkt, "plant_zero_seed": plant_zero_seed,
        "step0_total": len(step0),
        "step0_wash_by_teacher": dict(wash_by_teacher),
        "step0_total_by_teacher": dict(tot_by_teacher),
        "step0_wash_examples": [r for r in step0 if r["wash"]][:12],
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print("legs=%d steps=%d train=%d val=%d" % (n_legs, n_steps,
                                                train_steps, val_steps))
    print("teachers:", dict(teachers))
    print("U_OP:", dict(u_op))
    print("farmer_OP:", dict(farmer_op))
    print("M_OP:", dict(m_op))
    print("hand_count:", dict(sorted(hand_n.items())))
    print("market_count:", dict(sorted(mkt_n.items())))
    print("N1=%d N2=%d N3=%d U_TRUNC=%d M_TRUNC=%d" % (n1, n2, n3, utr, mtr))
    print("none f/h/m:", none_farmer, none_hands, none_mkt,
          "plant_zero_seed:", plant_zero_seed)
    print("step0: %d/%d wash; by teacher:" % (sum(wash_by_teacher.values()),
                                              len(step0)))
    for t in sorted(tot_by_teacher):
        print("  %s: %d/%d" % (t, wash_by_teacher[t], tot_by_teacher[t]))


if __name__ == "__main__":
    main()
