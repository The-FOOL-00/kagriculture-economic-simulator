# SPDX-License-Identifier: MIT
"""V32 P2 action interface: vocabularies, canonical candidates, exact mapping.

Grounded in kaggriculture 1.32.7 (no legal-enumeration API exists; invalid
actions are silent no-ops). The joint action (farmer + hands + market list)
is multi-slot by simulator construction: each slot gets an INDEPENDENT
pointer head over its own candidate set (no conditional chaining, hence
not autoregressive: all slots sample in parallel given the state).

- UNIT slots (farmer + each hand): one shared head over UNIT_VOCAB.
- MARKET slots (M=10 = env maxMarketOrdersPerTurn): per-slot head over
  MARKET_VOCAB; NO-OP emits [] (interior [] preserved: race-slot aligned).
"""

import hashlib
import json

UNIT_NOPARAM_OPS = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "DROP", "WATER",
                    "HARVEST", "FERTILIZE", "DIG", "BUILD_COOP",
                    "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
SHED_ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
              "MILK", "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]
MARKET_OPS = ["BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"]
MARKET_ITEMS = {"BUY_SEED": CROPS,
                "BUY_PRODUCT": ["WHEAT", "FERTILIZER"],
                "BUY_ANIMAL": ["GOOSE", "COW", "SHEEP"],
                "SELL": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                         "EGG", "MILK", "WOOL", "FERTILIZER"]}
M_MARKET_SLOTS = 10  # env maxMarketOrdersPerTurn default
# Observed max hands is 14 (W7x teachers hire deeper than V3/A7's 12).
# The simulator caps nothing; heads apply per actual hand (no truncation by
# construction). This assert-cap guards rollouts: exceeding it is a
# stop-and-investigate event, never silent truncation (§21).
MAX_HANDS_CAP = 16

# Opcodes in first-seen order (v32_encoder UNIT_OPS compatible superset).
UNIT_OPS = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "PLACE",
            "DROP", "PLANT", "WATER", "DIG", "WEED", "HARVEST",
            "COLLECT_FERTILIZER", "FERTILIZE", "FEED", "CARE",
            "BUILD_PASTURE", "BUILD_COOP"]


def build_unit_vocab(pickup_place_triples):
    """triples: iterable of (op, item, qty_or_None) observed in expert data,
    plus implicit-None form for every item. Returns list of (op,arg,qty)."""
    vocab = [(op, None, None) for op in UNIT_NOPARAM_OPS]
    vocab += [("PLANT", c, None) for c in CROPS]
    seen = set(vocab)
    for op in ("PICKUP", "PLACE"):
        for item in SHED_ITEMS:
            if (op, item, None) not in seen:
                vocab.append((op, item, None))
                seen.add((op, item, None))
    for op, item, qty in sorted(pickup_place_triples,
                                key=lambda t: (t[0], t[1], -1 if t[2] is None else t[2])):
        if op not in ("PICKUP", "PLACE") or item not in SHED_ITEMS:
            continue
        if (op, item, qty) not in seen:
            vocab.append((op, item, qty))
            seen.add((op, item, qty))
    return vocab


def build_market_vocab(qtys):
    """Full product over observed qty values (exact round-trip for experts)."""
    vocab = [("NOOP", None, None), ("HIRE", None, None),
             ("BUY_LAND", None, None)]
    for op in MARKET_OPS:
        for item in MARKET_ITEMS[op]:
            for q in sorted(qtys):
                vocab.append((op, item, q))
    return vocab


def unit_to_literal(cand):
    op, arg, qty = cand
    if arg is None:
        return [op]
    if qty is None:
        return [op, arg]
    return [op, arg, qty]


def market_to_literal(cand):
    op, item, qty = cand
    if op == "NOOP":
        return []
    if op in ("HIRE", "BUY_LAND"):
        return [op]
    return [op, item, qty]


def unit_from_literal(act):
    """Map a unit action list to a canonical (op,arg,qty) triple or None."""
    if not isinstance(act, list) or not act:
        return None
    op = act[0]
    if op in UNIT_NOPARAM_OPS:
        return (op, None, None)
    if op == "PLANT" and len(act) >= 2 and act[1] in CROPS:
        return (op, act[1], None)
    if op in ("PICKUP", "PLACE") and len(act) >= 2 and act[1] in SHED_ITEMS:
        if len(act) >= 3:
            try:
                return (op, act[1], int(act[2]))
            except (TypeError, ValueError):
                return None
        return (op, act[1], None)
    return None


def market_from_literal(order):
    if not isinstance(order, list) or len(order) == 0:
        return ("NOOP", None, None)
    op = order[0]
    if op in ("HIRE", "BUY_LAND"):
        return (op, None, None)
    if op in MARKET_OPS and len(order) >= 3 and order[1] in MARKET_ITEMS[op]:
        try:
            return (op, order[1], int(order[2]))
        except (TypeError, ValueError):
            return None
    return None


def candidate_hash(cand):
    return hashlib.sha256(json.dumps(cand, sort_keys=True).encode()).hexdigest()


def emit_market_list(slot_cands):
    """Slot candidates -> market order list. Interior [] preserved (race
    alignment); trailing [] stripped (provably harmless)."""
    orders = [market_to_literal(c) for c in slot_cands]
    while orders and orders[-1] == []:
        orders.pop()
    return orders


def plant_mask(unit_vocab, seeds):
    """1.0 = masked (provably-noop: zero seeds, order-independent)."""
    return [1.0 if (op == "PLANT" and (seeds or {}).get(arg, 0) <= 0) else 0.0
            for op, arg, _ in unit_vocab]
