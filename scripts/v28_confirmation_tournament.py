# SPDX-License-Identifier: MIT
"""V28: virgin confirmation tournament, A7 vs V3 (hermetic adapters).

Usage:
  v28_confirmation_tournament.py [--seeds START:END] [--out FILE]
                                 [--mode pool|serial] [--workers N]
                                 [--fresh-subprocess]

- Default cohort: virgin 249530..249569 x seats {0,1} = 80 matches.
- pool mode: ProcessPoolExecutor with max_tasks_per_child=1, i.e. every
  match runs in a FRESH worker process (no worker reuse, no ordering
  dependence possible). Default workers=9 (V27 parity).
- serial mode: same-process sequential execution (parity control).
- --fresh-subprocess: each match in its own `sys.executable` invocation
  (strongest isolation; used for the independent audit subset).
- Checkpointed, resumable by key; refuses to run if any frozen digest
  differs. No AEC, no tuning, no seed-specific behavior.

A7 = V27AblationAdapter("V27-ABL-A7") frozen bytes (see V28_A7_FREEZE.md).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")

# Frozen digests (V28_A7_FREEZE.md / V28_BASELINE_FREEZE.md).
A7_FILE_SHA = "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
P3_ADAPTER_SHA = "ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195"
V3_ADAPTER_SHA = "a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135"
INTERFACE_SHA = "1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091"
UTILS_SHA = "53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404"
CONFIG_SHA = "14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
ENGINE_VERSION = "1.32.7"

WORKER_NONCE = None


def _worker_init():
    global WORKER_NONCE
    WORKER_NONCE = uuid.uuid4().hex


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_frozen():
    base = os.path.join(REPO_ROOT, "aec", "backbone")
    assert sha256_file(os.path.join(base, "v27_ablation_adapters.py")) == A7_FILE_SHA, "A7 drift"
    assert sha256_file(os.path.join(base, "v25_p3_adapter.py")) == P3_ADAPTER_SHA, "P3-adapter drift"
    assert sha256_file(os.path.join(base, "v3_adapter.py")) == V3_ADAPTER_SHA, "V3-adapter drift"
    assert sha256_file(os.path.join(base, "interface.py")) == INTERFACE_SHA, "interface drift"
    assert sha256_file(os.path.join(base, "utils.py")) == UTILS_SHA, "utils drift"
    assert sha256_file(os.path.join(REPO_ROOT, "aec", "config.py")) == CONFIG_SHA, "config drift"
    assert sha256_file(os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")) == V3_SHA, "V3 drift"
    import kaggle_environments
    assert kaggle_environments.__version__ == ENGINE_VERSION, kaggle_environments.__version__


def compact(env):
    n = len(env.steps)
    money = [[], []]
    struct = [[], []]
    for i in range(n):
        for s in (0, 1):
            farm = env.steps[i][s]["observation"]["farms"][s]
            money[s].append(farm.get("money", 0.0))
            if i % 12 == 0:
                tiles = farm.get("tiles", []) or []
                plant = past = 0
                for row in tiles:
                    for t in row:
                        if isinstance(t, dict):
                            if t.get("kind") == "PLANT":
                                plant += 1
                            elif t.get("kind") == "PASTURE":
                                past += 1
                struct[s].append([len(farm.get("hands", []) or []),
                                  plant, past,
                                  len(farm.get("unlocked_quadrants", []) or [])])
    return {"money": money, "struct12": struct}


def run_one(spec):
    """Run one A7-vs-V3 match. Adapters constructed fresh inside the worker."""
    seed, seat = spec["seed"], spec["seat"]
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    assert a7.call_v3_at_step0 is True and a7.open_units == 30
    assert a7.dispatch is False and a7.rewrite_step0_wash is True
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: a7.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b] if seat == 0 else [b, a])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    delta = cand_r - base_r
    acts = [s[seat].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    money = compact(env)
    money_digest = hashlib.sha256(json.dumps(money["money"]).encode()).hexdigest()
    return {"key": "V28:%d:%d" % (seed, seat), "seed": seed, "seat": seat,
            "cand": "V27-ABL-A7", "base": "V3_STANDALONE",
            "cand_reward": cand_r, "base_reward": base_r, "delta": delta,
            "winner": "A7" if delta > 0 else ("V3" if delta < 0 else "TIE"),
            "tie_exact": delta == 0,
            "action_digest": digest, "money_digest": money_digest,
            "engine_version": ENGINE_VERSION,
            "cand_digest": A7_FILE_SHA, "base_digest": V3_SHA,
            "cand_flags": {"call_v3_at_step0": True, "open_units": 30,
                           "dispatch": False, "rewrite_step0_wash": True},
            "step0_rewritten": bool(a7.step0_rewritten),
            "step0_unexpected_shape": bool(a7.step0_unexpected_shape),
            "pid": os.getpid(), "worker_nonce": WORKER_NONCE,
            "mode": spec.get("mode", "pool"),
            "duration_sec": dur, "compact": money}


def run_one_subprocess(seed, seat, timeout=900):
    """Run one match in a fully independent interpreter invocation."""
    code = (
        "import json,sys; sys.path.insert(0,%r); "
        "from v28_confirmation_tournament import run_one, assert_frozen;"
        "assert_frozen();"
        "print(json.dumps(run_one({'seed':%d,'seat':%d,'mode':'fresh-subprocess'})))"
    ) % (os.path.join(REPO_ROOT, "scripts"), seed, seat)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, timeout=timeout, cwd=REPO_ROOT,
                       env=dict(os.environ))
    if p.returncode != 0:
        raise RuntimeError("subprocess match failed: %s" % p.stderr[-2000:])
    return json.loads(p.stdout.strip().splitlines()[-1])


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="249530:249569")
    ap.add_argument("--out", default="v28_raw_results.jsonl")
    ap.add_argument("--mode", default="pool", choices=["pool", "serial"])
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--fresh-subprocess", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    seeds = list(range(lo, hi + 1))
    out_path = os.path.join(RESULTS, args.out)
    done = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["key"])
    queue = [{"seed": s, "seat": t, "mode": args.mode}
             for s in seeds for t in (0, 1)
             if "V28:%d:%d" % (s, t) not in done]
    print("v28 seeds=%d..%d queued=%d done=%d mode=%s workers=%d fresh_subprocess=%s"
          % (lo, hi, len(queue), len(done), args.mode, args.workers,
             args.fresh_subprocess), flush=True)
    if not queue:
        return
    t_start = time.time()
    n = 0
    with open(out_path, "a", encoding="utf-8") as f_out:
        if args.fresh_subprocess:
            for spec in queue:
                rec = run_one_subprocess(spec["seed"], spec["seat"])
                f_out.write(json.dumps(rec) + "\n")
                f_out.flush()
                n += 1
                if n % 5 == 0:
                    print("... %d/%d (%.0fs)" % (n, len(queue), time.time() - t_start),
                          flush=True)
        elif args.mode == "serial":
            for spec in queue:
                rec = run_one(spec)
                f_out.write(json.dumps(rec) + "\n")
                f_out.flush()
                n += 1
                if n % 5 == 0:
                    print("... %d/%d (%.0fs)" % (n, len(queue), time.time() - t_start),
                          flush=True)
        else:
            with ProcessPoolExecutor(max_workers=args.workers,
                                     max_tasks_per_child=1,
                                     initializer=_worker_init) as ex:
                futs = {ex.submit(run_one, spec): spec for spec in queue}
                for fut in as_completed(futs):
                    try:
                        rec = fut.result()
                    except Exception as e:
                        print("ERROR %r" % e, flush=True)
                        continue
                    f_out.write(json.dumps(rec) + "\n")
                    f_out.flush()
                    n += 1
                    if n % 10 == 0:
                        print("... %d/%d (%.0fs)" % (n, len(queue), time.time() - t_start),
                              flush=True)
    print("v28 elapsed %.1fs wrote %d" % (time.time() - t_start, n), flush=True)
    recs = [json.loads(line) for line in open(out_path) if line.strip()]
    import statistics
    ds = [r["delta"] for r in recs]
    print("n=%d mean=%+.2f median=%+.1f sd=%.1f min=%+.0f max=%+.0f" % (
        len(ds), statistics.mean(ds), statistics.median(ds),
        statistics.stdev(ds) if len(ds) > 1 else 0.0, min(ds), max(ds)))


if __name__ == "__main__":
    main()
