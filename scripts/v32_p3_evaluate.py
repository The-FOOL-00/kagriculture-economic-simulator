# SPDX-License-Identifier: MIT
"""V32 P3 checkpoint eval: deterministic policy legs vs opponent panel.

Mirrors scripts/v32_p2_evaluate.py (P3 predictor + native decode).
Usage: v32_p3_evaluate.py --ckpt NPZ --tag TAG --out JSONL --seeds LO:HI
       --opps CSV [--seats 0,1] [--workers N] [--deterministic 0/1]
Records per leg: seed/opp/seat/cash/win + money curve + step-0 market +
wash flag. Quarantine enforced. No training.
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


def _worker_init(ckpt_path, norm_json):
    import sys as _s
    _s.path.insert(0, REPO_ROOT)
    _s.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    import numpy as _np
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    from v32.p2.features import Normalizer as _N
    from v32.p3.models import P3Policy as _P
    from v32.p3.rollout import Predictor as _Pr
    _W["model"] = _P(157, 12)
    d = _np.load(ckpt_path, allow_pickle=True)
    _W["model"].load_state_dict(
        {k: _t.tensor(v) for k, v in d.items() if k != "meta"})
    _W["model"].eval()
    _W["pred"] = _Pr(_W["model"], _N.from_json(norm_json))
    _W["nonce"] = uuid.uuid4().hex


def _run_one(spec):
    from kaggle_environments import make
    from v32_common import check_seed_allowed, expert_digest, load_agent
    from v32.p2.essentials import essentialize
    from v32.p3.rollout import Predictor
    check_seed_allowed(spec["seed"])
    ag = load_agent(spec["opp"])
    pred = _W["pred"]
    env = make("kaggriculture", configuration={"seed": spec["seed"]})
    pred.reset()
    steps = []
    det = spec["deterministic"]

    def learner_act(obs, cfg=None):
        pr = pred.step(essentialize(obs, spec["seat"]),
                       deterministic=det)
        steps.append(pr)
        return pr["action"]

    def opp_act(obs, cfg=None):
        return ag.act(obs, cfg)

    agents = [learner_act, opp_act] if spec["seat"] == 0 else \
        [opp_act, learner_act]
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0
    mine = float(env.steps[-1][spec["seat"]]["reward"])
    theirs = float(env.steps[-1][1 - spec["seat"]]["reward"])
    m0 = steps[0]["action"].get("market") or []
    ops0 = [o[0] for o in m0 if isinstance(o, list) and o]
    wash0 = (any(o in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL") for o in ops0)
             and "SELL" in ops0)
    return {
        "key": "V32P3EV:%s:%s:%d:%d" % (spec["tag"], spec["opp"],
                                        spec["seed"], spec["seat"]),
        "tag": spec["tag"], "seed": spec["seed"], "opp": spec["opp"],
        "seat": spec["seat"], "my_cash": mine, "opp_cash": theirs,
        "win": 1.0 if mine > theirs else (0.0 if mine < theirs else 0.5),
        "opp_digest": expert_digest(spec["opp"]),
        "duration_sec": dur, "worker_nonce": _W["nonce"],
        "n_steps": len(steps),
        "mean_entropy": sum(s["entropy"] for s in steps) / len(steps),
        "mean_value": sum(s["value"] for s in steps) / len(steps),
        "step0_market": m0, "step0_wash": wash0,
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
    ap.add_argument("--deterministic", type=int, default=1)
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
                              "seat": seat,
                              "deterministic": bool(args.deterministic)})
    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    print("V32 P3 eval %s: %d legs -> %s" % (args.tag, len(specs), args.out),
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
            if "V32P3EV:%s:%s:%d:%d" % (s["tag"], s["opp"], s["seed"], s["seat"])
            not in done]
    print("V32 P3 eval: %d done, %d to run" % (len(done), len(todo)), flush=True)
    if not todo:
        return
    out = open(args.out, "a", buffering=1)
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_worker_init,
                             initargs=(args.ckpt, norm)) as ex:
        futs = {ex.submit(_run_one, s): s for s in todo}
        n = 0
        for fut in as_completed(futs):
            out.write(json.dumps(fut.result()) + "\n")
            n += 1
            if n % 10 == 0:
                print("V32 P3 eval: %d/%d" % (n, len(todo)), flush=True)
    out.close()
    print("V32 P3 eval: complete %d legs" % len(todo), flush=True)


if __name__ == "__main__":
    main()
