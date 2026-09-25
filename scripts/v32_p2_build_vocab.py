# SPDX-License-Identifier: MIT
"""V32 P2 vocab builder: scan expert actions -> frozen candidate vocabs.

Scans results/v32_p2_bc_legs.jsonl (+ /tmp/v32_traj.jsonl EXP-2 actions for
extra coverage). Writes results/v32_p2_vocab.json. Fails loudly on unknown
opcodes (TEST 11 input). Pure analysis; runs no matches.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2 import actions as A  # noqa: E402

OPS = sorted(set(A.UNIT_OPS) | {"HIRE", "BUY_LAND", "BUY_SEED",
                                "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "NOOP"})
ITEMS = sorted(set(A.SHED_ITEMS) | set(A.CROPS))


def _scan_unit(u, trips, unknown):
    c = A.unit_from_literal(u)
    if c is None:
        unknown["unit:%r" % (u,)] += 1
        return
    if c[0] in ("PICKUP", "PLACE"):
        trips.add(c)


def _scan_market(o, qtys, unknown):
    if not isinstance(o, list) or len(o) == 0:
        return
    c = A.market_from_literal(o)
    if c is None:
        unknown["market:%r" % (o,)] += 1
        return
    if c[0] in A.MARKET_OPS:
        qtys.add(c[2])


def main():
    from collections import Counter
    trips, qtys, unknown = set(), set(), Counter()
    n_legs = n_steps = 0
    p = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    for line in open(p):
        leg = json.loads(line)
        n_legs += 1
        for side in ("rows0", "rows1"):
            for row in leg[side]:
                n_steps += 1
                act = row["a"] or {}
                _scan_unit(act.get("farmer"), trips, unknown)
                for h in (act.get("hands") or []):
                    _scan_unit(h, trips, unknown)
                for o in (act.get("market") or []):
                    _scan_market(o, qtys, unknown)
    q2 = os.path.join("/tmp", "v32_traj.jsonl")
    if os.path.exists(q2):
        for line in open(q2):
            rec = json.loads(line)
            for side in ("rows_left", "rows_right"):
                for row in rec[side]:
                    _scan_unit(row.get("farmer"), trips, unknown)
                    for h in (row.get("hands") or []):
                        _scan_unit(h, trips, unknown)
                    for o in (row.get("market") or []):
                        _scan_market(o, qtys, unknown)
    unit_vocab = A.build_unit_vocab(trips)
    market_vocab = A.build_market_vocab(qtys)
    out = {"ops": OPS, "items": ITEMS,
           "unit_vocab": [list(c) for c in unit_vocab],
           "market_vocab": [list(c) for c in market_vocab],
           "market_qtys": sorted(qtys),
           "n_legs": n_legs, "n_steps": n_steps,
           "unknown": dict(unknown)}
    wp = os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")
    with open(wp, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("legs=%d steps=%d unit=%d market=%d qtys=%d unknown=%s" % (
        n_legs, n_steps, len(unit_vocab), len(market_vocab), len(qtys),
        dict(unknown)))
    print("wrote", wp)


if __name__ == "__main__":
    main()
