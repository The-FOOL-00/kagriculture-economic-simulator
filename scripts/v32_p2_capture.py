# SPDX-License-Identifier: MIT
"""V32 P2 BC capture: expert legs -> compact raw essentials per step per seat.

Usage: v32_p2_capture.py --out FILE --seeds LO:HI --pairs L:R,L:R [--workers N]

Records, per step per seat, compact RAW essentials (not 90-vec) so P2's
multi-timescale temporal features can be computed offline/online:
  step/day/hour, money, farmer pos, hands pos, quads, hires_today,
  tile histogram (12 ints), per-unit tile codes, shed, seeds, inventories,
  prices, market inventory, shops unlocked, opp money/hands/quads/plant/
  pasture/weed (public), own action {farmer,hands,market}.
Leg header carries terminal rewards (offline labels for the §13 check).
Quarantine + frozen digests enforced. No torch dependency (numpy-free).
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

from v32_common import ENGINE_VERSION, assert_frozen, check_seed_allowed  # noqa: E402
from v32_common import expert_digest, load_agent  # noqa: E402
from v32.p2.essentials import essentialize  # noqa: E402 (single code path)

WORKER_NONCE = None


class Recorder:
    def __init__(self, expert, seat):
        self.expert = expert
        self.seat = seat
        self.rows = []

    def act(self, obs, cfg=None):
        act = self.expert.act(obs, cfg)
        self.rows.append({"e": essentialize(obs, self.seat),
                          "a": {"farmer": act.get("farmer"),
                                "hands": act.get("hands"),
                                "market": act.get("market")}})
        return act


def _worker_init():
    global WORKER_NONCE
    global _W
    import uuid as _u
    _W = _u.uuid4().hex


def run_one(spec):
    from kaggle_environments import make
    seed = spec["seed"]
    check_seed_allowed(seed)
    left = Recorder(load_agent(spec["left"]), 0)
    right = Recorder(load_agent(spec["right"]), 1)
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([lambda o, c=None: left.act(o, c),
             lambda o, c=None: right.act(o, c)])
    dur = time.time() - t0
    return {
        "key": "V32P2BC:%s:%s:%d" % (spec["left"], spec["right"], seed),
        "seed": seed, "left": spec["left"], "right": spec["right"],
        "left_reward": env.steps[-1][0]["reward"],
        "right_reward": env.steps[-1][1]["reward"],
        "duration_sec": dur, "engine_version": ENGINE_VERSION,
        "left_digest": expert_digest(spec["left"]),
        "right_digest": expert_digest(spec["right"]),
        "rows0": left.rows, "rows1": right.rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    pairs = [p.split(":") for p in args.pairs.split(",")]
    specs = []
    for s in range(lo, hi + 1):
        for l, r in pairs:
            specs.append({"seed": s, "left": l, "right": r})
            specs.append({"seed": s, "left": r, "right": l})
    print("V32 P2 capture: %d legs seeds %d..%d -> %s"
          % (len(specs), lo, hi, args.out), flush=True)
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
            if "V32P2BC:%s:%s:%d" % (s["left"], s["right"], s["seed"]) not in done]
    print("V32 P2 capture: %d already done, %d to run" % (len(done), len(todo)),
          flush=True)
    if not todo:
        return
    out = open(args.out, "a", buffering=1)
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_worker_init,
                             max_tasks_per_child=1) as ex:
        futs = {ex.submit(run_one, s): s for s in todo}
        n = 0
        for fut in as_completed(futs):
            out.write(json.dumps(fut.result()) + "\n")
            n += 1
            if n % 10 == 0:
                print("V32 P2 capture: %d/%d" % (n, len(todo)), flush=True)
    out.close()
    print("V32 P2 capture: complete %d legs" % len(todo), flush=True)


if __name__ == "__main__":
    main()
