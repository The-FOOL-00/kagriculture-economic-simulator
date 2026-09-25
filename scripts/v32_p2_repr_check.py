# SPDX-License-Identifier: MIT
"""V32 P2 §13 representation-sufficiency check (diagnostic, offline only).

Question: can the FROZEN P2 feature representation (Groups A-D, computed
from information observable at time t) distinguish trajectories that later
diverge economically? Targets are offline labels ONLY (never policy inputs).

Probe: multinomial logistic (torch, deterministic) per time bin:
  t<=24, 25-100, 101-200, 201-300, 301+.
Targets: (a) terminal cash bucket (5), (b) win/loss, (c) pair-level hi/lo,
(d) own wash-size class (GROUP-C plumbing sanity: knowable from t>=1).
Split by SEED: fit on BC-train legs, probe on BC-val legs (249647-249649).
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import torch  # noqa: E402

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: E402
from v32.p2.features import EpisodeFeatures, Normalizer  # noqa: E402

BINS = [(0, 24), (25, 100), (101, 200), (201, 300), (301, 719)]
N_CASH_BUCKETS = 5


def wash_class(market0):
    for o in (market0 or []):
        if isinstance(o, list) and o and o[0] == "BUY_PRODUCT" and \
                len(o) > 2 and o[1] == "WHEAT":
            try:
                return int(o[2])
            except (TypeError, ValueError):
                return -1
    return -1


def collect():
    norm = Normalizer.from_json(json.load(open(
        os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    data = []  # (split, t, feat, cash, win, level_hi, wash)
    for leg in load_legs(os.path.join(REPO_ROOT, "results",
                                      "v32_p2_bc_legs.jsonl")):
        split = "val" if leg["seed"] in BC_VAL_SEEDS else "train"
        for side, me, op in (("rows0", leg["left_reward"], leg["right_reward"]),
                             ("rows1", leg["right_reward"], leg["left_reward"])):
            rows = leg[side]
            w = wash_class((rows[0]["a"] or {}).get("market"))
            fb = EpisodeFeatures()
            prev = None
            for row in rows:
                f = norm.transform([fb.update(row["e"], prev)])[0]
                prev = row["a"] or {}
                data.append((split, int(row["e"]["step"]), f, me,
                             1.0 if me > op else 0.0, me + op, w))
    return data


def fit_probe(Xtr, Ytr, Xva, Yva, nclass, seed=0):
    import numpy as _np
    torch.manual_seed(seed)
    Xtr = torch.tensor(_np.asarray(Xtr), dtype=torch.float32)
    Ytr = torch.tensor(Ytr, dtype=torch.long)
    Xva = torch.tensor(_np.asarray(Xva), dtype=torch.float32)
    lin = torch.nn.Linear(Xtr.shape[1], nclass)
    opt = torch.optim.Adam(lin.parameters(), lr=1e-2, weight_decay=1e-3)
    loss = torch.nn.CrossEntropyLoss()
    for _ in range(300):
        opt.zero_grad()
        loss(lin(Xtr), Ytr).backward()
        opt.step()
    with torch.no_grad():
        pred = lin(Xva).argmax(-1).tolist()
    acc = sum(p == y for p, y in zip(pred, Yva)) / len(Yva)
    maj = max(Yva.count(c) for c in set(Yva)) / len(Yva)
    return acc, maj


def main():
    import numpy as np
    data = collect()
    tr = [d for d in data if d[0] == "train"]
    va = [d for d in data if d[0] == "val"]
    cash = sorted(d[3] for d in tr)
    qs = [cash[int(len(cash) * q / N_CASH_BUCKETS)] for q in range(N_CASH_BUCKETS)]
    med_level = sorted(d[5] for d in tr)[len(tr) // 2]

    def bucket(c):
        for i in range(N_CASH_BUCKETS - 1, -1, -1):
            if c >= qs[i]:
                return i
        return 0

    washes = sorted({d[6] for d in tr})
    wid = {w: i for i, w in enumerate(washes)}
    print("cash quintiles: %s med_level=%.0f washes=%s" % (
        [round(q) for q in qs], med_level, washes))
    print("bin        cash(acc/maj)  win  level  wash")
    for lo, hi in BINS:
        Xtr = [d[2] for d in tr if lo <= d[1] <= hi][::3]
        Xva = [d[2] for d in va if lo <= d[1] <= hi][::3]
        if not Xtr or not Xva:
            print("%3d-%3d  no data" % (lo, hi))
            continue
        outs = []
        for tgt, nc in (("cash", N_CASH_BUCKETS), ("win", 2), ("level", 2),
                        ("wash", len(washes))):
            if tgt == "cash":
                Ytr = [bucket(d[3]) for d in tr if lo <= d[1] <= hi][::3]
                Yva = [bucket(d[3]) for d in va if lo <= d[1] <= hi][::3]
            elif tgt == "win":
                Ytr = [int(d[4]) for d in tr if lo <= d[1] <= hi][::3]
                Yva = [int(d[4]) for d in va if lo <= d[1] <= hi][::3]
            elif tgt == "level":
                Ytr = [int(d[5] > med_level) for d in tr if lo <= d[1] <= hi][::3]
                Yva = [int(d[5] > med_level) for d in va if lo <= d[1] <= hi][::3]
            else:
                Ytr = [wid[d[6]] for d in tr if lo <= d[1] <= hi][::3]
                Yva = [wid.get(d[6], 0) for d in va if lo <= d[1] <= hi][::3]
            acc, maj = fit_probe(Xtr, Ytr, Xva, Yva, nc)
            outs.append("%.2f/%.2f" % (acc, maj))
        print("%3d-%3d  %s" % (lo, hi, "  ".join(outs)))


if __name__ == "__main__":
    main()
