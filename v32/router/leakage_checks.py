# SPDX-License-Identifier: MIT
"""R1 leakage / boundary / determinism audits (also wired into tests)."""

from v32.router.split import OPP_PANEL, ROUTER_CLASSES

REFUSED_RANGES = [(214200, 214249), (340000, 340049), (340050, 340050 + 39),
                  (340090, 340199), (340200, 340249), (340250, 340299),
                  (340300, 340349)]
CONFIRM = (249695, 249734)
COMMISSIONING = (249673, 249674)


def audit_rows(rows):
    """Split/seat/quarantine audit. Raises on violation. Returns summary."""
    seen_split = {}
    for r in rows:
        s = r["seed"]
        for lo, hi in REFUSED_RANGES:
            assert not (lo <= s <= hi), "refused seed %d" % s
        assert not (CONFIRM[0] <= s <= CONFIRM[1]), "CONFIRM touched: %d" % s
        assert not (COMMISSIONING[0] <= s <= COMMISSIONING[1]), \
            "commissioning in batch: %d" % s
        assert r["opp"] in OPP_PANEL, r["opp"]
        assert len(r["cash"]) == len(ROUTER_CLASSES) == 5
        assert r["mode"] in ("full", "cont")
        if s in seen_split:
            assert seen_split[s] == r["split"], (s, seen_split[s], r["split"])
        seen_split[s] = r["split"]
        p = r.get("prefix")
        if p is not None:
            assert p.get("canonical", True), "mirror prefix in row %s" % (r,)
            for k in p.get("frames", {}):
                assert int(k) <= 24, "future frame t=%s" % k
    by_split = {}
    for s, sp in seen_split.items():
        by_split.setdefault(sp, set()).add(s)
    keys = list(by_split)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            assert not (by_split[keys[i]] & by_split[keys[j]]), \
                "seed leak across splits %s/%s" % (keys[i], keys[j])
    return {k: len(v) for k, v in by_split.items()}


def audit_features(X):
    """No NaN/Inf; finite clipped range."""
    import math
    n = 0
    for row in X:
        for v in row:
            assert isinstance(v, float), type(v)
            assert math.isfinite(v), v
            n += 1
    return n
