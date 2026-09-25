# SPDX-License-Identifier: MIT
"""V32 P2 checkpoint eval: deterministic policy legs vs opponent panel.

Usage: v32_p2_evaluate.py --ckpt NPZ --out JSONL --seeds LO:HI
       --opps CSV [--seats 0,1] [--workers N]
Records per leg: seed/opp/seat/cash/win + money curve + action stats.
Quarantine enforced. No training.
"""

import argparse
import json
import os
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

_W = {}


def _worker_init(ckpt_path, vocab, norm_json):
    import sys as _s
    _s.path.insert(0, REPO_ROOT)
    _s.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    import numpy as _np
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    from v32.p2.features import Normalizer as _N
    from v32.p2.models import P2Policy as _P
    from v32.p2.rollout import Predictor as _Pr
    _W["norm"] = _N.from_json(norm_json)
    _W["uvoc"] = [tuple(c) for c in vocab["unit_vocab"]]
    _W["mvoc"] = [tuple(c) for c in vocab["market_vocab"]]
    _W["model"] = _P(157, 12, _W["uvoc"], _W["mvoc"], vocab["ops"], vocab["items"])
    d = _np.load(ckpt_path, allow_pickle=True)
    _W["model"].load_state_dict(
        {k: _t.tensor(v) for k, v in d.items() if k != "meta"})
    _W["model"].eval()
    _W["pred"] = _Pr(_W["model"], _W["norm"], _W["uvoc"], _W["mvoc"])
    _W["nonce"] = uuid.uuid4().hex


def _run_one(spec):
    from kaggle_environments import make
    from v32_common import check_seed_allowed, expert_digest, load_agent
    from v32.p2.rollout import run_episode
    check_seed_allowed(spec["seed"])
    ag = load_agent(spec["opp"])
    t0 = time.time()
    steps, mine, theirs = run_episode(
        lambda s: make("kaggriculture", configuration={"seed": s}),
        spec["seed"], spec["seat"], _W["pred"], ag)
    # first-divergence + timing diagnostics
    return {
        "key": "V32P2EV:%s:%s:%d:%d" % (spec["tag"], spec["opp"],
                                        spec["seed"], spec["seat"]),
        "tag": spec["tag"], "seed": spec["seed"], "opp": spec["opp"],
        "seat": spec["seat"], "my_cash": mine, "opp_cash": theirs,
        "win": 1.0 if mine > theirs else (0.0 if mine < theirs else 0.5),
        "opp_digest": expert_digest(spec["opp"]),
        "duration_sec": time.time() - t0, "worker_nonce": _W["nonce"],
        "n_steps": len(steps),
        "mean_entropy": sum(s["entropy"] for s in steps) / len(steps),
        "mean_value": sum(s["value"] for s in steps) / len(steps),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--opps", required=True)
    ap.add_argument("--seats", default="0,1")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    from v32_common import assert_frozen, check_seed_allowed
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    specs = []
    for s in range(lo, hi + 1):
        for o in args.opps.split(","):
            for seat in [int(x) for x in args.seats.split(",")]:
                specs.append({"tag": args.tag, "seed": s, "opp": o,
                              "seat": seat})
    vocab = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")))
    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    print("V32 P2 eval %s: %d legs -> %s" % (args.tag, len(specs), args.out),
          flush=True)
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(json.loads(line)["key"])
                    except (KeyError, ValueError):
                        pass
    todo = [s for s in specs
            if "V32P2EV:%s:%s:%d:%d" % (s["tag"], s["opp"], s["seed"], s["seat"])
            not in done]
    print("V32 P2 eval: %d done, %d to run" % (len(done), len(todo)), flush=True)
    if not todo:
        return
    out = open(args.out, "a", buffering=1)
    # NOTE: no max_tasks cap (respawn wedged the pool at exactly
    # workers x cap; workers hold no cross-leg state: fresh experts per leg,
    # predictor.reset() per episode).
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_worker_init,
                             initargs=(args.ckpt, vocab, norm)) as ex:
        futs = {ex.submit(_run_one, s): s for s in todo}
        n = 0
        for fut in as_completed(futs):
            out.write(json.dumps(fut.result()) + "\n")
            n += 1
            if n % 10 == 0:
                print("V32 P2 eval: %d/%d" % (n, len(todo)), flush=True)
    out.close()
    print("V32 P2 eval: complete %d legs" % len(todo), flush=True)


if __name__ == "__main__":
    main()
