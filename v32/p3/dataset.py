# SPDX-License-Identifier: MIT
"""V32 P3 BC dataset: capture legs -> (features, factorized targets).

Features replayed through the P2 ONLINE builder in step order (identical code
path as P2 training, P3 rollout, and eval — Groups A-D, v32p2feat-v1).
Targets are P3 native factorized tuples (v32.p3.codec). BC-val = P2-TRAIN
seeds 249647-249649 (same split as P2 BC).
"""

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: F401 (same split)
from v32.p2.features import EpisodeFeatures, unit_ctx
from v32.p3 import codec as C


def build_samples(leg, seat_rows, teacher):
    """Replay one seat's rows through the online builder. Yields samples."""
    fb = EpisodeFeatures()
    prev = None
    for row in seat_rows:
        ess = row["e"]
        feat = fb.update(ess, prev)
        act = row["a"] or {}
        n_u = 1 + len(ess.get("hands", []) or [])
        enc = C.encode_action(act, n_u - 1)
        assert not enc["flags"], (leg["seed"], ess.get("step"), enc["flags"])
        uxo = [(o, a, q) for o, a, q in enc["u"]]
        yield {"feat": feat,
               "uctx": [unit_ctx(ess, j) for j in range(n_u)],
               "u_op": [t[0] for t in uxo], "u_arg": [t[1] for t in uxo],
               "u_qty": [t[2] for t in uxo],
               "m_op": [t[0] for t in enc["m"]],
               "m_item": [t[1] for t in enc["m"]],
               "m_qty": [t[2] for t in enc["m"]],
               "step": ess.get("step"), "seed": leg["seed"],
               "teacher": teacher}
        prev = act
