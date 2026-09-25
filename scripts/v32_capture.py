# SPDX-License-Identifier: MIT
"""V32 EXP-2: expert trajectory capture for imitation/router probes.

Usage: v32_capture.py --out FILE --seeds START:END --pair L:R [--ticks 12]

Records per-step (encoded_obs, farmer_op, hands_ops, market_ops) for BOTH seats
via a recording wrapper. Experts stay frozen; only observations/actions are
logged. Quarantine enforced (TRAIN/DEV only, never CONFIRM/protected).
"""

import argparse
import json
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from v32_common import assert_frozen, check_seed_allowed, load_agent  # noqa: E402
from v32_encoder import ENCODER_VERSION, encode_obs  # noqa: E402


class Recorder:
    def __init__(self, expert, seat):
        self.expert = expert
        self.seat = seat
        self.rows = []

    def act(self, obs, cfg=None):
        t0 = time.time()
        act = self.expert.act(obs, cfg)
        dt = time.time() - t0
        try:
            vec = encode_obs(obs, self.seat)
        except Exception as e:  # noqa: BLE001 - schema drift must degrade loudly
            vec = None
            print("ENCODE-FAIL step=%s: %r" % (obs.get("step"), e), flush=True)
        self.rows.append({"step": obs.get("step"), "obs": vec,
                          "farmer": act.get("farmer"), "hands": act.get("hands"),
                          "market": act.get("market"), "act_sec": dt})
        return act


def capture_pair(left_id, right_id, seed):
    from kaggle_environments import make
    check_seed_allowed(seed)
    left = Recorder(load_agent(left_id), 0)
    right = Recorder(load_agent(right_id), 1)
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([lambda o, c=None: left.act(o, c),
             lambda o, c=None: right.act(o, c)])
    dur = time.time() - t0
    return {"seed": seed, "left": left_id, "right": right_id,
            "left_reward": env.steps[-1][0]["reward"],
            "right_reward": env.steps[-1][1]["reward"],
            "duration_sec": dur, "encoder": ENCODER_VERSION,
            "rows_left": left.rows, "rows_right": right.rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--pair", default="E2_A7:E0_V3")
    args = ap.parse_args()
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    left_id, right_id = args.pair.split(":")
    n_pairs = 0
    t0 = time.time()
    with open(args.out, "w", buffering=1) as f:
        for seed in range(lo, hi + 1):
            for l, r in ((left_id, right_id), (right_id, left_id)):
                rec = capture_pair(l, r, seed)
                f.write(json.dumps(rec) + "\n")
                n_pairs += len(rec["rows_left"]) + len(rec["rows_right"])
                print("captured %s:%s:%d (%.0f pairs, %.1fs)"
                      % (l, r, seed, len(rec["rows_left"]) + len(rec["rows_right"]),
                         rec["duration_sec"]), flush=True)
    dt = time.time() - t0
    print("V32 capture: %d pairs in %.1fs = %.0f pairs/s -> %s"
          % (n_pairs, dt, n_pairs / dt, args.out), flush=True)


if __name__ == "__main__":
    main()
