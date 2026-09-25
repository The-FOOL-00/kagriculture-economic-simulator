# SPDX-License-Identifier: MIT
"""V32 P2 compact raw essentials from a live observation (shared by capture,
rollout, and eval — one code path)."""

CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


def _tile_code(t):
    if t is None:
        return 0
    if t == "LOCKED":
        return 1
    if not isinstance(t, dict):
        return 1
    k = t.get("kind")
    if k == "WEED":
        return 2
    if k == "PLANT":
        try:
            return 3 if float(t.get("yield_units", 0)) > 0 else 4
        except (TypeError, ValueError):
            return 4
    if "animal" in t:
        return 8 if t.get("fertilizer_available") else 7
    if k == "COOP":
        return 5
    if k == "PASTURE":
        return 6
    return 1


def _tile_hist(tiles):
    plant = [0] * 5
    past = weed = coop = anim = empty = 0
    for row in (tiles or []):
        for t in row:
            if t is None:
                empty += 1
            elif t == "LOCKED":
                pass
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT" and t.get("crop") in CROPS:
                    plant[CROPS.index(t["crop"])] += 1
                elif k == "PASTURE":
                    past += 1
                elif k == "WEED":
                    weed += 1
                elif k == "COOP":
                    coop += 1
                if "animal" in t:
                    anim += 1
    return plant + [past, weed, coop, anim, empty]


def _get(o, k, default=None):
    if isinstance(o, dict):
        return o.get(k, default)
    return getattr(o, k, default)


def essentialize(obs, seat):
    p = int(seat)
    farms = _get(obs, "farms", []) or []
    farm = farms[p] if p < len(farms) else {}
    ofarm = farms[1 - p] if (1 - p) < len(farms) else {}
    priv = _get(obs, "private", {}) or {}
    town = _get(obs, "town", {}) or {}
    market = _get(obs, "market", {}) or {}
    tiles = _get(farm, "tiles", []) or []
    otiles = _get(ofarm, "tiles", []) or []
    units = [(_get(farm, "farmer", [4, 4]) or [4, 4])] + \
        list(_get(farm, "hands", []) or [])

    def code_at(pos):
        try:
            return _tile_code(tiles[int(pos[1])][int(pos[0])])
        except (TypeError, ValueError, IndexError):
            return 1

    oh = _tile_hist(otiles)
    return {
        "step": _get(obs, "step"), "day": _get(obs, "day"),
        "hour": _get(obs, "hour"),
        "money": _get(farm, "money", 0.0),
        "farmer": list((_get(farm, "farmer", [4, 4]) or [4, 4])[:2]),
        "hands": [list(h[:2]) for h in (_get(farm, "hands", []) or [])],
        "quads": len(_get(farm, "unlocked_quadrants", []) or []),
        "hires": _get(farm, "hires_today", 0),
        "thist": _tile_hist(tiles),
        "ucode": [code_at(u) for u in units],
        "shed": dict(_get(priv, "shed", {}) or {}),
        "seeds": dict(_get(priv, "seeds", {}) or {}),
        "inv": [dict(i or {}) for i in (_get(priv, "inventories", []) or [])],
        "prices": dict(_get(market, "prices", {}) or {}),
        "mkt_inv": dict(_get(market, "inventory", {}) or {}),
        "shops": list(_get(town, "unlocked_shops", []) or []),
        "o_money": _get(ofarm, "money", 0.0),
        "o_hands": len(_get(ofarm, "hands", []) or []),
        "o_quads": len(_get(ofarm, "unlocked_quadrants", []) or []),
        "o_plant": sum(oh[:5]), "o_past": oh[5], "o_weed": oh[6],
    }
