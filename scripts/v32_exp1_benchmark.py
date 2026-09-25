# SPDX-License-Identifier: MIT
"""V32 EXP-1: expert-population benchmark (round-robin + parity + sanity).

Usage:
  v32_exp1_benchmark.py [--out FILE] [--mode pool|serial] [--workers N]
                        [--only PAIR,...] [--seeds START:END]

- Default: round-robin over CORE_RR (9 experts, 36 pairs) x V32_EXP1 seeds
  (249635..249640) x seats {0,1} = 432 legs, plus A7-vs-AST parity (12 legs)
  plus V3-vs-PASS sanity (4 legs on first 2 seeds).
- pool mode: ProcessPoolExecutor, max_tasks_per_child=1 (fresh process per leg).
- Checkpointed, resumable by key; asserts frozen digests; enforces quarantine.
- No AEC tuning, no learning, no CONFIRM touch.
"""

import argparse
import hashlib
import itertools
import json
import os
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from v32_common import (CORE_RR, ENGINE_VERSION, V32_EXP1, assert_frozen,  # noqa: E402
                        check_seed_allowed, expert_digest, load_agent, telemetry)

RESULTS = os.path.join(REPO_ROOT, "results")
WORKER_NONCE = None


def _worker_init():
    global WORKER_NONCE
    WORKER_NONCE = uuid.uuid4().hex


def run_one(spec):
    """One mirrored leg. Experts constructed fresh inside the worker."""
    from kaggle_environments import make
    seed = spec["seed"]
    check_seed_allowed(seed)
    left_id, right_id = spec["left"], spec["right"]
    left = load_agent(left_id)
    right = load_agent(right_id)
    a = lambda o, c=None: left.act(o, c)  # noqa: E731
    b = lambda o, c=None: right.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    acts = [[s[0].get("action"), s[1].get("action")] for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    tel = telemetry(env)
    money_digest = hashlib.sha256(json.dumps(tel["money"]).encode()).hexdigest()
    return {
        "key": "V32EXP1:%s:%s:%d" % (left_id, right_id, seed),
        "seed": seed, "left": left_id, "right": right_id,
        "left_reward": r0, "right_reward": r1, "delta": r0 - r1,
        "winner": "LEFT" if r0 > r1 else ("RIGHT" if r1 > r0 else "TIE"),
        "action_digest": digest, "money_digest": money_digest,
        "engine_version": ENGINE_VERSION,
        "left_digest": expert_digest(left_id), "right_digest": expert_digest(right_id),
        "pid": os.getpid(), "worker_nonce": WORKER_NONCE,
        "mode": spec.get("mode", "pool"), "duration_sec": dur,
        "telemetry": tel,
    }


def build_specs(seeds, only=None):
    specs = []
    pairs = list(itertools.combinations(CORE_RR, 2))
    for l, r in pairs:
        for seed in seeds:
            specs.append({"left": l, "right": r, "seed": seed})
            specs.append({"left": r, "right": l, "seed": seed})
    for seed in seeds:  # packaging parity: A7 adapter vs standalone file
        specs.append({"left": "E2_A7", "right": "E9_AST", "seed": seed})
        specs.append({"left": "E9_AST", "right": "E2_A7", "seed": seed})
    for seed in seeds[:2]:  # weak-anchor sanity
        specs.append({"left": "E0_V3", "right": "E10_PASS", "seed": seed})
        specs.append({"left": "E10_PASS", "right": "E0_V3", "seed": seed})
    if only:
        want = set(only)
        specs = [s for s in specs
                 if "%s:%s" % (s["left"], s["right"]) in want]
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(RESULTS, "v32_exp1.jsonl"))
    ap.add_argument("--mode", default="pool", choices=["pool", "serial"])
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--only", default=None, help="comma-separated LEFT:RIGHT pairs")
    ap.add_argument("--seeds", default="%d:%d" % V32_EXP1)
    args = ap.parse_args()

    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    seeds = list(range(lo, hi + 1))
    only = args.only.split(",") if args.only else None
    specs = build_specs(seeds, only)
    print("V32 EXP-1: %d legs, seeds %d..%d, mode=%s workers=%d -> %s"
          % (len(specs), lo, hi, args.mode, args.workers, args.out), flush=True)

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
            if "V32EXP1:%s:%s:%d" % (s["left"], s["right"], s["seed"]) not in done]
    print("V32 EXP-1: %d already done, %d to run" % (len(done), len(todo)), flush=True)
    if not todo:
        return

    out = open(args.out, "a", buffering=1)
    if args.mode == "serial":
        for s in todo:
            s["mode"] = "serial"
            out.write(json.dumps(run_one(s)) + "\n")
            print("did %s:%s:%d" % (s["left"], s["right"], s["seed"]), flush=True)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.workers,
                                 initializer=_worker_init,
                                 max_tasks_per_child=1) as ex:
            futs = {}
            for s in todo:
                s["mode"] = "pool"
                futs[ex.submit(run_one, s)] = s
            n = 0
            for fut in as_completed(futs):
                rec = fut.result()
                out.write(json.dumps(rec) + "\n")
                n += 1
                if n % 20 == 0:
                    print("V32 EXP-1: %d/%d" % (n, len(todo)), flush=True)
    out.close()
    print("V32 EXP-1: complete", flush=True)


if __name__ == "__main__":
    main()
