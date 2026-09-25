# SPDX-License-Identifier: MIT
"""V32 P3 native action codec: lossless literal <-> factorized targets.

Schema: V32_P3_ACTION_SCHEMA.md / .json (v32p3-a1), grounded in
kaggriculture 1.32.7 (_apply_unit_action, _parse_order, _process_market).

Encode maps a recorded native literal to one target per head; decode maps
head predictions back to the exact simulator-native literal. Round-trip is
literal identity modulo three documented normalizations (all semantically
inert per simulator source; occurrences counted, G1 requires 0 unexplained
semantic mismatches):
  N1: unknown unit opcode (incl. WEED, which has no simulator branch) -> PASS.
  N2: out-of-vocabulary qty int -> nearest observed value.
  N3: trailing args beyond the schema -> dropped (never read by the sim).
"""

import bisect
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMA_PATH = os.path.join(REPO_ROOT, "V32_P3_ACTION_SCHEMA.json")

U_OP = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "DROP", "WATER",
        "HARVEST", "FERTILIZE", "DIG", "BUILD_COOP", "BUILD_PASTURE",
        "FEED", "COLLECT_FERTILIZER", "CARE", "PLANT", "PICKUP", "PLACE"]
U_NOPARAM = set(U_OP[:15])
U_ARG = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
         "MILK", "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]
CROPS = U_ARG[:5]
# IMPLICIT = absent qty element (semantically identical to explicit 1).
U_QTY = ["IMPLICIT", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 18,
         1000]
M_OP = ["NOOP", "HIRE", "BUY_LAND", "BUY_SEED", "BUY_PRODUCT",
        "BUY_ANIMAL", "SELL"]
M_QTY_OPS = {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"}
M_ITEM = list(U_ARG)
M_QTY = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
         18, 19, 20, 21, 22, 23, 24, 25, 29, 30, 31, 32, 33, 35, 36,
         38, 39, 40, 47, 48, 50, 55, 57, 59, 60, 63, 65, 69, 71, 73,
         74, 75, 77, 79, 80, 81, 82, 83, 84, 85, 88, 89, 90, 91, 92,
         93, 96, 100, 983, 984, 985, 986, 988, 992, 996, 997, 998,
         999, 1000]
M_MARKET_SLOTS = 10
MAX_HANDS_CAP = 16  # assert-cap (stop-and-investigate, never truncation)

_U_OP_ID = {o: i for i, o in enumerate(U_OP)}
_U_ARG_ID = {a: i for i, a in enumerate(U_ARG)}
_U_QTY_ID = {q: i for i, q in enumerate(U_QTY)}
_M_OP_ID = {o: i for i, o in enumerate(M_OP)}
_M_ITEM_ID = {a: i for i, a in enumerate(M_ITEM)}
_M_QTY_ID = {q: i for i, q in enumerate(M_QTY)}
_U_QTY_INTS = sorted(q for q in U_QTY if isinstance(q, int))


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _nearest(sorted_vals, v):
    i = bisect.bisect_left(sorted_vals, v)
    if i <= 0:
        return sorted_vals[0]
    if i >= len(sorted_vals):
        return sorted_vals[-1]
    lo, hi = sorted_vals[i - 1], sorted_vals[i]
    return lo if v - lo <= hi - v else hi


def _coerce_int(v):
    """int() exactly as the simulator applies it (bool is int; float floors)."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    raise ValueError(v)


def encode_unit(lit):
    """Native unit literal -> (op, arg, qty, flags).

    Missing/None/non-list/empty literal -> PASS (simulator-identical no-op).
    flags: subset of {"N1", "N3"} (normalizations applied).
    """
    flags = []
    if not isinstance(lit, list) or not lit:
        return (_U_OP_ID["PASS"], 0, 0, flags)
    op = lit[0]
    if op not in _U_OP_ID:
        flags.append("N1")
        return (_U_OP_ID["PASS"], 0, 0, flags)
    if op in U_NOPARAM:
        if len(lit) > 1:
            flags.append("N3")
        return (_U_OP_ID[op], 0, 0, flags)
    if op == "PLANT":
        if len(lit) < 2 or lit[1] not in CROPS:
            # Malformed PLANT is a simulator silent no-op; represent the
            # closest meaningful target so decode stays in-schema.
            flags.append("N3")
            return (_U_OP_ID["PASS"], 0, 0, flags)
        if len(lit) > 2:
            flags.append("N3")
        return (_U_OP_ID[op], _U_ARG_ID[lit[1]], 0, flags)
    # PICKUP / PLACE
    if len(lit) < 2 or lit[1] not in _U_ARG_ID:
        flags.append("N3")
        return (_U_OP_ID["PASS"], 0, 0, flags)
    if len(lit) < 3:
        return (_U_OP_ID[op], _U_ARG_ID[lit[1]], 0, flags)
    try:
        q = _coerce_int(lit[2])
    except (ValueError, TypeError):
        # Simulator would RAISE here (no try/except in PICKUP/PLACE);
        # such a literal is unexecutable — normalize to PASS, flag it.
        flags.append("N3")
        return (_U_OP_ID["PASS"], 0, 0, flags)
    if len(lit) > 3:
        flags.append("N3")
    if q not in _U_QTY_ID:
        flags.append("N2")
        q = _nearest(_U_QTY_INTS, q)
    return (_U_OP_ID[op], _U_ARG_ID[lit[1]], _U_QTY_ID[q], flags)


def decode_unit(op, arg, qty):
    """Head predictions -> exact simulator-native unit literal."""
    o = U_OP[op]
    if o in U_NOPARAM:
        return [o]
    if o == "PLANT":
        return [o, U_ARG[arg]]
    qv = U_QTY[qty]
    if qv == "IMPLICIT":
        return [o, U_ARG[arg]]
    return [o, U_ARG[arg], qv]


def encode_market(lit):
    """Native market order literal -> (op, item, qty, flags)."""
    flags = []
    if not isinstance(lit, list) or not lit:
        return (_M_OP_ID["NOOP"], 0, _M_QTY_ID[0], flags)
    op = lit[0]
    if op not in _M_OP_ID or op == "NOOP":
        if op != "NOOP":
            flags.append("N1")
        return (_M_OP_ID["NOOP"], 0, _M_QTY_ID[0], flags)
    if op in ("HIRE", "BUY_LAND"):
        if len(lit) > 1:
            flags.append("N3")
        return (_M_OP_ID[op], 0, _M_QTY_ID[0], flags)
    if len(lit) < 3 or lit[1] not in _M_ITEM_ID:
        # Malformed qty-order: simulator parses to None (silent no-op).
        # Encode as NOOP (decodes to [] which also parses to None).
        flags.append("N3")
        return (_M_OP_ID["NOOP"], 0, _M_QTY_ID[0], flags)
    try:
        q = _coerce_int(lit[2])
    except (ValueError, TypeError):
        flags.append("N3")
        return (_M_OP_ID["NOOP"], 0, _M_QTY_ID[0], flags)
    if len(lit) > 3:
        flags.append("N3")
    if q not in _M_QTY_ID:
        flags.append("N2")
        q = _nearest(M_QTY, q)
    return (_M_OP_ID[op], _M_ITEM_ID[lit[1]], _M_QTY_ID[q], flags)


def decode_market(op, item, qty):
    """Head predictions -> exact simulator-native market order literal."""
    o = M_OP[op]
    if o == "NOOP":
        return []
    if o in ("HIRE", "BUY_LAND"):
        return [o]
    return [o, M_ITEM[item], M_QTY[qty]]


def encode_action(native, n_hands):
    """Full joint action -> per-slot targets + flags.

    native: {"farmer": lit, "hands": [lit...], "market": [lit...]}.
    n_hands: live hand count (hands beyond it are unrepresentable by the
    simulator too — extra elements are ignored there as well).
    Market orders beyond slot 10 are dropped (simulator truncates identically).
    Returns {"u": [(op,arg,qty)...], "m": [(op,item,qty)...], "flags": [...]};
    u has 1+n_hands entries, m has M_MARKET_SLOTS entries.
    """
    assert n_hands <= MAX_HANDS_CAP, n_hands
    native = native if isinstance(native, dict) else {}
    units = [native.get("farmer")] + list(native.get("hands") or [])
    mkt = native.get("market") or []
    if not isinstance(mkt, list):
        mkt = []
    out_u, out_m, flags = [], [], []
    for j in range(1 + n_hands):
        lit = units[j] if j < len(units) else ["PASS"]
        o, a, q, fl = encode_unit(lit)
        out_u.append((o, a, q))
        flags.extend("U%d:%s" % (j, f) for f in fl)
    for s in range(M_MARKET_SLOTS):
        lit = mkt[s] if s < len(mkt) else []
        o, i, q, fl = encode_market(lit)
        out_m.append((o, i, q))
        flags.extend("M%d:%s" % (s, f) for f in fl)
    if len(mkt) > M_MARKET_SLOTS:
        flags.append("M:TRUNC")
    if len(units) > 1 + n_hands:
        flags.append("U:TRUNC")
    return {"u": out_u, "m": out_m, "flags": flags}


def decode_action(u_targ, m_targ):
    """Per-slot targets -> exact simulator-native joint action dict."""
    ulits = [decode_unit(o, a, q) for o, a, q in u_targ]
    mlits = [decode_market(o, i, q) for o, i, q in m_targ]
    while mlits and mlits[-1] == []:
        mlits.pop()
    return {"farmer": ulits[0], "hands": ulits[1:], "market": mlits}


def plant_crop_masked(seeds, crop):
    """True iff PLANT_crop is provably a no-op (zero seeds of that crop).

    NOTE: P3 a1 applies NO loss/output masking (silent no-ops are learned;
    decode is pure literal reconstruction). The seeds==0 PLANT rule remains
    exactly maskable (schema §6.4-C1) and this helper exists for analysis
    and for a documented fallback (per-crop PLANT split) if G2 fails on
    PLANT slots specifically. See V32_P3_MODEL_ARCHITECTURE.md.
    """
    return (seeds or {}).get(crop, 0) <= 0
