# SPDX-License-Identifier: MIT
"""V32 P2 normalizer: fit TRAIN-only stats, freeze to JSON.

Fits on BC-train legs (P2-TRAIN seeds excluding BC-val 249647-249649).
Writes results/v32_p2_norm.json. Pure analysis; runs no matches.
"""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: E402
from v32.p2.features import EpisodeFeatures, Normalizer, schema_names  # noqa: E402


def main():
    import numpy as np
    feats = []
    n = 0
    for leg in load_legs(os.path.join(REPO_ROOT, "results",
                                      "v32_p2_bc_legs.jsonl")):
        if leg["seed"] in BC_VAL_SEEDS:
            continue
        for side in ("rows0", "rows1"):
            fb = EpisodeFeatures()
            prev = None
            for row in leg[side]:
                feats.append(fb.update(row["e"], prev))
                prev = (row["a"] or {})
                n += 1
    X = np.asarray(feats, dtype=float)
    norm = Normalizer()
    norm.fit(X)
    d = norm.to_json()
    d["schema_version"] = "v32p2feat-v1"
    d["schema"] = schema_names()
    d["n_fit"] = n
    d["val_seeds_excluded"] = sorted(BC_VAL_SEEDS)
    blob = json.dumps(d, sort_keys=True)
    d["sha256"] = hashlib.sha256(blob.encode()).hexdigest()
    out = os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")
    with open(out, "w") as f:
        json.dump(d, f, indent=1, sort_keys=True)
    print("fit n=%d dim=%d -> %s sha=%s" % (n, X.shape[1], out, d["sha256"][:16]))


if __name__ == "__main__":
    main()
