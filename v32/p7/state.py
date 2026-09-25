# SPDX-License-Identifier: MIT
"""V32 P7 normalized simulator-state distance (pure, deterministic).

Compares two ess snapshots component-wise with per-component normalization so
no single large-magnitude field (e.g. cash) dominates. Weights are documented
below and fixed for the phase (see V32_P7_STATE_TRAJECTORY.md).

Components (each in ~[0, 1+] after normalization):
- position: farmer Manhattan distance / 18 (board diameter) + mean paired-hand
  Manhattan / 18 (unpaired hands count as full diameter).
- hands: |hand count diff| / 16 (MAX_HANDS_CAP).
- cash: |money diff| / 3000 (starting capital scale).
- inventory: mean per-key |diff| over union of carried goods / 20.
- livestock: |shed+carried animal diff| (COW/SHEEP/GOOSE) / 10.
- crops: |thist plant-count diff| summed / 20 + pasture/coop/stocked diff / 6.
- market: |unlocked shop count diff| / 4 (prices are exogenous per seed and
  excluded from the distance; opponent trading effects are out of scope).

Total = weighted mean with WEIGHTS below.
"""

ANIMALS = ("COW", "SHEEP", "GOOSE")
BOARD_DIAMETER = 18.0
CASH_SCALE = 3000.0

WEIGHTS = {
    "position": 2.0,
    "hands": 1.0,
    "cash": 1.0,
    "inventory": 1.0,
    "livestock": 2.0,
    "crops": 1.0,
    "market": 0.5,
}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _manhattan(a, b):
    return abs(_f(a[0]) - _f(b[0])) + abs(_f(a[1]) - _f(b[1]))


def state_distance(a, b):
    """Normalized component distances + weighted total. Pure function."""
    comp = {}
    comp["position"] = _manhattan(a.get("farmer", [4, 4]) or [4, 4],
                                  b.get("farmer", [4, 4]) or [4, 4]) / BOARD_DIAMETER
    ha = a.get("hands", []) or []
    hb = b.get("hands", []) or []
    if ha or hb:
        paired = sum(_manhattan(x, y) for x, y in zip(ha, hb))
        unpaired = abs(len(ha) - len(hb)) * BOARD_DIAMETER
        comp["position"] += (paired + unpaired) / BOARD_DIAMETER / max(
            1, max(len(ha), len(hb)))
    comp["hands"] = abs(len(ha) - len(hb)) / 16.0
    comp["cash"] = abs(_f(a.get("money", 0.0)) - _f(b.get("money", 0.0))) / CASH_SCALE
    ia = a.get("inv", []) or []
    ib = b.get("inv", []) or []
    tot_a, tot_b = {}, {}
    for inv in ia:
        if isinstance(inv, dict):
            for k, v in inv.items():
                tot_a[k] = tot_a.get(k, 0.0) + _f(v)
    for inv in ib:
        if isinstance(inv, dict):
            for k, v in inv.items():
                tot_b[k] = tot_b.get(k, 0.0) + _f(v)
    keys = set(tot_a) | set(tot_b)
    comp["inventory"] = (sum(abs(tot_a.get(k, 0.0) - tot_b.get(k, 0.0))
                             for k in keys) / 20.0 / max(1, len(keys))
                         if keys else 0.0)
    sa = a.get("shed", {}) or {}
    sb = b.get("shed", {}) or {}
    comp["livestock"] = sum(
        abs(_f(sa.get(k, 0)) + tot_a.get(k, 0.0)
            - _f(sb.get(k, 0)) - tot_b.get(k, 0.0)) for k in ANIMALS) / 10.0
    ta = list(a.get("thist", [0] * 10) or [0] * 10)
    tb = list(b.get("thist", [0] * 10) or [0] * 10)
    comp["crops"] = (sum(abs(_f(x) - _f(y)) for x, y in zip(ta[:5], tb[:5]))
                     / 20.0
                     + sum(abs(_f(x) - _f(y)) for x, y in zip(ta[5:9], tb[5:9]))
                     / 6.0)
    comp["market"] = abs(len(a.get("shops", []) or [])
                         - len(b.get("shops", []) or [])) / 4.0
    total = sum(comp[k] * WEIGHTS[k] for k in WEIGHTS) / sum(WEIGHTS.values())
    return {"components": comp, "total": total}
