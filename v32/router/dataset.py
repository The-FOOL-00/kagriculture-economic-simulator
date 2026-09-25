# SPDX-License-Identifier: MIT
"""R1 dataset assembly: label legs -> (seed, opponent) rows.

Row: {seed, opp, split, cash[5], win[5], margin[5], prefix, mode}.
- full rows on EXP-1 TRAIN seeds reuse results/v32_exp1.jsonl directed legs
  (+ self-play + V3 prefixes from results/v32_router_full_c.jsonl).
- full rows elsewhere come from results/v32_router_full_{a,b}.jsonl.
- cont rows come from results/v32_router_cont_{a,b,c}.jsonl.
- prefix for (seed, opp) always comes from the V3 full leg's opening
  (canonical seat-0 only; mirror prefixes are never used).
"""

import json
import os

from v32.router.split import OPP_PANEL, ROUTER_CLASSES, split_of

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS = os.path.join(REPO_ROOT, "results")

FULL_FILES = ["v32_router_full_a.jsonl", "v32_router_full_b.jsonl",
              "v32_router_full_c.jsonl"]
CONT_FILES = ["v32_router_cont_a.jsonl", "v32_router_cont_b.jsonl",
              "v32_router_cont_c.jsonl"]
LOCKED_FULL = "v32_router_full_locked.jsonl"
LOCKED_CONT = "v32_router_cont_locked.jsonl"


def _iter_jsonl(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_rows(include_locked=False):
    """Assemble all rows. Returns (rows_full, rows_cont)."""
    # new-grid legs: (mode, seed, cls, opp) -> record (canonical only)
    legs = {}
    files = list(FULL_FILES)
    cfiles = list(CONT_FILES)
    if include_locked:
        files.append(LOCKED_FULL)
        cfiles.append(LOCKED_CONT)
    for fn in files + cfiles:
        p = os.path.join(RESULTS, fn)
        if not os.path.exists(p):
            continue
        for r in _iter_jsonl(p):
            if r.get("mirror"):
                continue
            legs[(r["mode"], r["seed"], r["cls"], r["opp"])] = r
    # EXP-1 directed legs for TRAIN seeds 249635-249640 (full mode only)
    exp1 = {}
    for r in _iter_jsonl(os.path.join(RESULTS, "v32_exp1.jsonl")):
        if r.get("engine_version") != "1.32.7":
            continue
        s = r["seed"]
        if not (249635 <= s <= 249640):
            continue
        l, rr = r["left"], r["right"]
        if l in ROUTER_CLASSES and rr in OPP_PANEL:
            exp1[(s, l, rr)] = (r["left_reward"], r["right_reward"])
        if rr in ROUTER_CLASSES and l in OPP_PANEL:
            exp1[(s, rr, l)] = (r["right_reward"], r["left_reward"])
    # V3 prefixes: new-grid V3 full legs (canonical)
    prefix = {}
    for (mode, s, c, o), r in legs.items():
        if mode == "full" and c == "E0_V3" and r["prefix"].get("canonical"):
            prefix[(s, o)] = r["prefix"]

    rows_full, rows_cont = [], []
    seeds = set()
    for (mode, s, c, o) in legs:
        seeds.add(s)
    seeds.update(s for (s, c, o) in exp1)
    for s in sorted(seeds):
        sp = split_of(s)
        if sp is None:
            continue
        for o in OPP_PANEL:
            for mode, store in (("full", rows_full), ("cont", rows_cont)):
                cash, win, margin, ok = [], [], [], True
                for c in ROUTER_CLASSES:
                    if mode == "full" and (s, c, o) in exp1 and (
                            mode, s, c, o) not in legs:
                        mine, theirs = exp1[(s, c, o)]
                    elif (mode, s, c, o) in legs:
                        r = legs[(mode, s, c, o)]
                        mine, theirs = r["my_cash"], r["opp_cash"]
                    else:
                        ok = False
                        break
                    cash.append(mine)
                    margin.append(mine - theirs)
                    win.append(1.0 if mine > theirs else
                               (0.0 if mine < theirs else 0.5))
                if not ok:
                    continue
                store.append({"seed": s, "opp": o, "split": sp, "mode": mode,
                              "cash": cash, "win": win, "margin": margin,
                              "prefix": prefix.get((s, o))})
    return rows_full, rows_cont


def rows_complete(rows, seeds, opps=OPP_PANEL):
    """Missing (seed, opp) combos for a row list (coverage audit)."""
    have = {(r["seed"], r["opp"]) for r in rows}
    return [(s, o) for s in seeds for o in opps if (s, o) not in have]
