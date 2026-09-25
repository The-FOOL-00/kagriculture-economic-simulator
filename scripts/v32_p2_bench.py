# SPDX-License-Identifier: MIT
"""V32 P2 §33 throughput bench: candidate counts + policy timing on real data.

Measures: unit/market candidate counts, hands distribution, forward-pass
latency (trunk + candidate encoding + scoring), full-step latency incl.
feature build. Writes results/v32_p2_bench.json. Pure analysis + timing.
"""

import json
import os
import sys
import time
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import torch  # noqa: E402

from v32.p2 import actions as A  # noqa: E402
from v32.p2.dataset import load_legs  # noqa: E402
from v32.p2.features import EpisodeFeatures, Normalizer, unit_ctx  # noqa: E402
from v32.p2.models import P2Policy, param_count  # noqa: E402


def main():
    vocab = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")))
    norm = Normalizer.from_json(json.load(open(
        os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    uvoc = [tuple(c) for c in vocab["unit_vocab"]]
    mvoc = [tuple(c) for c in vocab["market_vocab"]]
    torch.manual_seed(0)
    model = P2Policy(157, 12, uvoc, mvoc, vocab["ops"], vocab["items"])
    model.eval()
    print("params=%d unit_cand=%d market_cand=%d" % (
        param_count(model), len(uvoc), len(mvoc)))

    # gather real states (subsampled across legs/steps)
    states = []
    hands_c = Counter()
    mkt_c = Counter()
    for i, leg in enumerate(load_legs(os.path.join(
            REPO_ROOT, "results", "v32_p2_bc_legs.jsonl"))):
        if i % 6:
            continue
        for side in ("rows0", "rows1"):
            fb = EpisodeFeatures()
            prev = None
            for row in leg[side][::12]:
                e = row["e"]
                f = norm.transform([fb.update(e, prev)])[0]
                prev = row["a"] or {}
                n_u = 1 + len(e.get("hands", []) or [])
                states.append((f, [unit_ctx(e, j) for j in range(n_u)],
                               A.plant_mask(uvoc, e.get("seeds", {}) or {})))
                hands_c[len(e.get("hands", []) or [])] += 1
                mkt_c[len((row["a"] or {}).get("market") or [])] += 1
    print("hands dist:", dict(sorted(hands_c.items())))
    print("market-len dist:", dict(sorted(mkt_c.items())))

    # warmup then time single-state forwards (rollout regime: batch=1)
    def one(s):
        f, ux, mk = s
        st = torch.tensor([f], dtype=torch.float32)
        uc = torch.tensor([ux], dtype=torch.float32)
        vv = torch.ones(1, len(ux), dtype=torch.bool)
        mm = torch.tensor([mk], dtype=torch.float32)
        with torch.no_grad():
            return model.act(st, uc, vv, mm)
    for s in states[:5]:
        one(s)
    t0 = time.time()
    N = min(200, len(states))
    for s in states[:N]:
        one(s)
    dt = (time.time() - t0) / N * 1000
    print("forward+sample per step: %.1f ms (batch=1, %d states)" % (dt, N))
    print("=> policy-only ceiling: %.0f agent-steps/s single-process" % (1000 / dt))
    with open(os.path.join(REPO_ROOT, "results", "v32_p2_bench.json"), "w") as f:
        json.dump({"params": param_count(model), "unit_cand": len(uvoc),
                   "market_cand": len(mvoc), "ms_per_step": round(dt, 2),
                   "hands_dist": dict(hands_c),
                   "market_len_dist": dict(mkt_c)}, f, indent=1)


if __name__ == "__main__":
    main()
