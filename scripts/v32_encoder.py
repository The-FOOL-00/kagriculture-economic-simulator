# SPDX-License-Identifier: MIT
"""V32 state encoder v1 + action-vocabulary mask utilities.

Implements V32_STATE_ENCODER_SPEC.md / V32_ACTION_ENCODER_SPEC.md.
Pure functions of (observation, player). No seed, no RNG, no hidden state.

CORRECTION (2026-09-22, probe-grounded): obs['market'] DOES expose prices +
inventory ({prices, inventory} x 9 products), so the Market group uses real
prices instead of the shop/ledger proxies the spec draft assumed. Spec §5 gap
note is superseded for prices (encoder v1.1); shop + pressure features stay.
"""

ENCODER_VERSION = "v32enc-v1.1"

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
            "MILK", "WOOL", "FERTILIZER"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["COW", "SHEEP", "GOOSE"]

UNIT_OPS = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "PLACE",
            "DROP", "PLANT", "WATER", "DIG", "WEED", "HARVEST", "COLLECT_FERTILIZER",
            "FERTILIZE", "FEED", "CARE", "BUILD_PASTURE", "BUILD_COOP"]
MARKET_OPS = ["BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "HIRE", "SELL"]

V32_OBS_DIM = 90  # unstacked; frame stack handled by the model, not here.


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _tile_counts(tiles):
    plant = past = weed = dry = 0
    per_crop = {c: [0, 0, 0, 0.0] for c in CROPS}  # planted,growing,ready,yield
    for row in (tiles or []):
        for t in row:
            if not isinstance(t, dict):
                continue
            k = t.get("kind")
            if k == "PLANT":
                plant += 1
                c = t.get("crop")
                if c in per_crop:
                    v = per_crop[c]
                    v[0] += 1
                    y = _f(t.get("yield_units", 0))
                    v[3] += y
                    if y > 0:
                        v[2] += 1
                    else:
                        v[1] += 1
                if not t.get("watered_today", True):
                    dry += 1
            elif k == "PASTURE":
                past += 1
            elif k == "WEED":
                weed += 1
    free = 0
    for row in (tiles or []):
        for t in row:
            if t is None:
                free += 1
    return plant, past, weed, dry, free, per_crop


def encode_obs(observation, player):
    """Encode observable state -> 90 floats. See V32_STATE_ENCODER_SPEC.md.

    Reads ONLY: observation[step,day,hour,market,town], farms[player] (full),
    private (own), farms[1-player] PUBLIC farm fields. Never opponent private.
    """
    p = int(player)
    farms = observation.get("farms", []) or []
    farm = farms[p] if p < len(farms) else {}
    ofarm = farms[1 - p] if (1 - p) < len(farms) else {}
    priv = observation.get("private", {}) or {}
    town = observation.get("town", {}) or {}
    market = observation.get("market", {}) or {}
    prices = market.get("prices", {}) or {}
    mkt_inv = market.get("inventory", {}) or {}
    shed = priv.get("shed", {}) or {}
    seeds = priv.get("seeds", {}) or {}
    inventories = priv.get("inventories", []) or []

    step = _f(observation.get("step", 0))
    day = _f(observation.get("day", 0))
    money = _f(farm.get("money", 0.0))
    shed_total = sum(max(0.0, _f(v)) for v in shed.values())
    seeds_total = sum(max(0.0, _f(v)) for v in seeds.values())
    shops = len(town.get("unlocked_shops", []) or [])
    hands = farm.get("hands", []) or []
    n_hands = len(hands)
    carrying = sum(1 for inv in inventories
                   if isinstance(inv, dict) and sum(_f(v) for v in inv.values()) > 0)
    plant, past, weed, dry, free, per_crop = _tile_counts(farm.get("tiles", []))
    oplant, opast, oweed, _, _, _ = _tile_counts(ofarm.get("tiles", []))
    ohands = len(ofarm.get("hands", []) or [])
    omoney = _f(ofarm.get("money", 0.0))
    quads = len(farm.get("unlocked_quadrants", []) or [])
    oquads = len(ofarm.get("unlocked_quadrants", []) or [])

    # Global (8)
    g = [step / 720.0, day / 30.0, max(0.0, (720.0 - step)) / 720.0,
         money / 1e5, 0.0,  # cash_delta_12 filled by frame stacker (0 unstacked)
         shed_total / 1e5, seeds_total / 1e3, shops / 8.0]
    # Crop (24): per-crop planted/growing/ready/yield + totals
    c = []
    for crop in CROPS:
        v = per_crop[crop]
        c += [v[0] / 200.0, v[1] / 200.0, v[2] / 200.0, v[3] / 500.0]
    c += [plant / 100.0, (plant + past) / 100.0, dry / 100.0, weed / 100.0]
    # Livestock (10)
    feed_req = _f(shed.get("COW", 0)) * 2 + _f(shed.get("SHEEP", 0)) + _f(shed.get("GOOSE", 0)) * 0.5
    l = [_f(shed.get(a, 0)) / 20.0 for a in ANIMALS]
    l += [feed_req / 50.0, past / 100.0,
          past / max(1.0, (plant + past)),
          _f(shed.get("MILK", 0)) / 1e4, _f(shed.get("WOOL", 0)) / 1e4,
          _f(shed.get("EGG", 0)) / 1e4, 0.0]  # starvation flag: needs temporal ctx
    l = l[:10]
    # Workers (8)
    fx, fy = (farm.get("farmer", [4, 4]) or [4, 4])[:2]
    w = [n_hands / 12.0, _f(fx) / 10.0, _f(fy) / 10.0,
         carrying / max(1.0, n_hands + 1.0),
         _f(farm.get("hires_today", 0)) / 12.0, 0.0, 0.0, 0.0]
    # Land (6)
    la = [quads / 4.0, plant / 100.0, past / 100.0, free / 100.0,
          weed / 100.0, dry / 100.0]
    # Market (14): 9 prices + pressures (v1.1: real prices, observed schema)
    m = [_f(prices.get(pr, 0)) / 250.0 for pr in PRODUCTS]
    inv_vals = [_f(mkt_inv.get(pr, 0)) for pr in PRODUCTS]
    m += [sum(inv_vals) / 1e5, max(inv_vals + [0]) / 2e4,
          shed_total / 1e5, shops / 8.0, 0.0]
    m = m[:14]
    # Opponent-observable (16): public farm fields + shared market ONLY
    o = [min(1.0, max(0.0, omoney / 1e5)), oplant / 100.0, opast / 100.0,
         oweed / 100.0, ohands / 12.0, oquads / 4.0]
    o += [0.0] * 10  # sell-pressure/livestock/wash proxies need temporal ctx (stacker fills)
    o = o[:16]
    # Phase (4)
    ph = [1.0 if step < 60 else 0.0, 1.0 if 60 <= step < 480 else 0.0,
          1.0 if 480 <= step < 660 else 0.0, 1.0 if step >= 660 else 0.0]
    vec = g + c + l + w + la + m + o + ph
    assert len(vec) == V32_OBS_DIM, len(vec)
    return [max(-8.0, min(8.0, v)) for v in vec]


def validate_action(action, n_hands):
    """Check an action dict against the known vocabulary/arity.

    Returns (legal: bool, reason: str). This is the mask oracle used by
    test_v32_legal_mask and the BC/PPO mask builder.
    """
    if not isinstance(action, dict):
        return False, "not-a-dict"
    f = action.get("farmer")
    if not (isinstance(f, list) and f and f[0] in UNIT_OPS):
        return False, "bad-farmer-op:%r" % (f,)
    hands = action.get("hands")
    if not isinstance(hands, list) or len(hands) != n_hands:
        return False, "hands-arity:%s-vs-%d" % (len(hands) if isinstance(hands, list) else "?", n_hands)
    for u in hands:
        if not (isinstance(u, list) and u and u[0] in UNIT_OPS):
            return False, "bad-hand-op:%r" % (u,)
    mkt = action.get("market")
    if not isinstance(mkt, list):
        return False, "market-not-list"
    for o in mkt:
        if not (isinstance(o, list) and o and o[0] in MARKET_OPS):
            return False, "bad-market-op:%r" % (o,)
    return True, "ok"


def mask_for(n_hands, n_market_slots=8):
    """Return index-shape metadata for masked heads (no torch dependency).

    Shapes: farmer_op [U], farmer_arg [A] (op-conditioned, masked at runtime),
    hands_op [H, U], market [M, O*P*Q]. This function returns (U, H, M, O, P, Q).
    """
    return {"n_unit_ops": len(UNIT_OPS), "n_hands": n_hands,
            "n_market_slots": n_market_slots, "n_market_ops": len(MARKET_OPS),
            "n_products": len(PRODUCTS), "encoder": ENCODER_VERSION}
