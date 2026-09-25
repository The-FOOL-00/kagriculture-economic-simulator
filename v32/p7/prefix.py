# SPDX-License-Identifier: MIT
"""V32 P7 prefix extraction from recorded BC demonstrations.

Replays each seat's recorded rows through the SAME online builder code path as
P2 training / P3 rollout / P6 eval (EpisodeFeatures.update in step order), so
prefix features are bit-identical to build_samples() features for the same rows
(covered by tests/test_v32_p7.py::test_03).

No live teacher queries, no relabeling, no future-state access: labels are the
recorded native actions only.
"""

import copy

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: F401 (same split)
from v32.p2.features import EpisodeFeatures, unit_ctx
from v32.p3 import codec as C

PREFIX_HORIZONS = (4, 8, 12, 24)


def extract_prefix_steps(seat_rows, teacher, seed, H):
    """Replay rows 0..H through the online builder. Returns step records.

    Returns None if fewer than H+1 rows are available. Each record holds the
    recorded ess snapshot, online temporal features, per-unit contexts, native
    factorized targets, and the recorded native action. Pure function of the
    recorded rows (deterministic).
    """
    if len(seat_rows) < H + 1:
        return None
    fb = EpisodeFeatures()
    prev = None
    out = []
    for row in seat_rows[:H + 1]:
        ess = row["e"]
        feat = fb.update(ess, prev)
        act = row["a"] or {}
        n_u = 1 + len(ess.get("hands", []) or [])
        enc = C.encode_action(act, n_u - 1)
        assert not enc["flags"], (seed, ess.get("step"), enc["flags"])
        uxo = [(o, a, q) for o, a, q in enc["u"]]
        out.append({
            "step": ess.get("step"),
            "seed": seed,
            "teacher": teacher,
            "ess": copy.deepcopy(ess),
            "feat": list(feat),
            "uctx": [unit_ctx(ess, j) for j in range(n_u)],
            "u_op": [t[0] for t in uxo],
            "u_arg": [t[1] for t in uxo],
            "u_qty": [t[2] for t in uxo],
            "m_op": [t[0] for t in enc["m"]],
            "m_item": [t[1] for t in enc["m"]],
            "m_qty": [t[2] for t in enc["m"]],
            "action": copy.deepcopy(act),
        })
        prev = act
    return out


def iter_leg_prefixes(legs_path, horizons=PREFIX_HORIZONS):
    """Yield (leg_key, seat, teacher, H, steps) for every recorded seat.

    seat is 0/1 with teacher leg['left']/leg['right'].
    """
    for leg in load_legs(legs_path):
        for seat, (side, teacher) in enumerate(
                (("rows0", leg["left"]), ("rows1", leg["right"]))):
            rows = leg[side]
            for H in horizons:
                steps = extract_prefix_steps(rows, teacher, leg["seed"], H)
                if steps is not None:
                    yield (leg["key"], seat, teacher, H, steps)


def farmer_sequence(steps):
    """Farmer native literals for a prefix (for canonical tables)."""
    return [(s["step"], list((s["action"].get("farmer") or ["PASS"]))) for s in steps]


def market_sequence(steps):
    """Market native literals for a prefix (for canonical tables)."""
    return [(s["step"], [list(o) for o in (s["action"].get("market") or [])])
            for s in steps]


def hands_sequence(steps):
    """Hand native literals for a prefix (for canonical tables)."""
    return [(s["step"], [list(h or ["PASS"]) for h in
             (s["action"].get("hands") or [])]) for s in steps]
