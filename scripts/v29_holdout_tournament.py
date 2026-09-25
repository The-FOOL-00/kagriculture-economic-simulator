# SPDX-License-Identifier: MIT
"""V29: protected-holdout promotion tournament, four arms (hermetic adapters).

Usage:
  v29_holdout_tournament.py [--seeds START:END] [--arms A1,A2,A3,A4]
                            [--out FILE] [--mode pool|serial] [--workers N]
                            [--fresh-subprocess] [--allow-consumed-qual]

- Default cohort: protected holdout slice 340050..340089 (40 seeds).
- Arms: A1 = A7@0 vs V3@1 (40), A2 = V3@0 vs A7@1 (40),
        A3 = A7 vs A7 (40, one match yields both seats' cash),
        A4 = V3 vs V3 (40, one match yields both seats' cash).
  Total default: 160 matches.
- pool mode: ProcessPoolExecutor with max_tasks_per_child=1 (fresh worker
  process per match). Default workers=9 (V28 parity).
- serial mode: same-process sequential execution (parity control).
- --fresh-subprocess: each match in its own `sys.executable` invocation
  (strongest isolation; used for the independent re-run subset).
- --allow-consumed-qual: permit seeds < 340050 (consumed cohorts) for the
  preregistered isolation/parity qualification ONLY. Seeds >= 340090
  (protected remainder) are refused ALWAYS, with no override flag.
- Checkpointed, resumable by key; refuses to run if any frozen digest
  differs. No AEC, no tuning, no seed-specific behavior.

A7 = V27AblationAdapter("V27-ABL-A7") frozen bytes (see V29_A7_FREEZE.md).
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

# Frozen digests (V29_BASELINE_FREEZE.md / V29_A7_FREEZE.md).
A7_FILE_SHA = "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
P3_ADAPTER_SHA = "ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195"
V3_ADAPTER_SHA = "a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135"
INTERFACE_SHA = "1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091"
UTILS_SHA = "53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404"
CONFIG_SHA = "14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
ENGINE_VERSION = "1.32.7"

SIM_DIGESTS = {"p3_adapter": P3_ADAPTER_SHA, "v3_adapter": V3_ADAPTER_SHA,
               "interface": INTERFACE_SHA, "utils": UTILS_SHA,
               "config": CONFIG_SHA}

# Holdout governance (V29_PREREGISTRATION.md s3).
SLICE_LO, SLICE_HI = 340050, 340089
REMAINDER_LO = 340090

ARMS = ("A1", "A2", "A3", "A4")
A7_FLAGS = {"call_v3_at_step0": True, "open_units": 30,
            "dispatch": False, "rewrite_step0_wash": True}

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


def harness_digest():
    return sha256_file(os.path.join(REPO_ROOT, "scripts",
                                    "v29_holdout_tournament.py"))


def config_fingerprint():
    payload = {"protocol": "V29_A7_PROMOTION_HOLDOUT",
               "engine_version": ENGINE_VERSION,
               "cand_variant": "V27-ABL-A7", "cand_flags": A7_FLAGS,
               "base": "V3_STANDALONE",
               "isolation": "fresh-process-per-match",
               "arms": list(ARMS)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()
                          ).hexdigest()


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


def check_seed_allowed(seed, allow_consumed_qual):
    if seed >= REMAINDER_LO:
        raise RuntimeError("GOVERNANCE REFUSAL: seed %d touches protected "
                           "remainder 340090..340199 (no override)" % seed)
    if not (SLICE_LO <= seed <= SLICE_HI) and not allow_consumed_qual:
        raise RuntimeError("GOVERNANCE REFUSAL: seed %d outside V29 slice "
                           "340050..340089 without --allow-consumed-qual"
                           % seed)


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


def _fresh_a7():
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    assert a7.call_v3_at_step0 is True and a7.open_units == 30
    assert a7.dispatch is False and a7.rewrite_step0_wash is True
    return a7


def run_one(spec):
    """Run one V29 match. Adapters constructed fresh inside the worker."""
    seed, arm = spec["seed"], spec["arm"]
    if arm == "A1":
        left, right = _fresh_a7(), V3BackboneAdapter()
        cand, base, seat = "V27-ABL-A7", "V3_STANDALONE", 0
        a7s = (left,)
    elif arm == "A2":
        left, right = V3BackboneAdapter(), _fresh_a7()
        cand, base, seat = "V27-ABL-A7", "V3_STANDALONE", 1
        a7s = (right,)
    elif arm == "A3":
        left, right = _fresh_a7(), _fresh_a7()
        cand, base, seat = "V27-ABL-A7", "V27-ABL-A7", 0
        a7s = (left, right)
    elif arm == "A4":
        left, right = V3BackboneAdapter(), V3BackboneAdapter()
        cand, base, seat = "V3_STANDALONE", "V3_STANDALONE", 0
        a7s = ()
    else:
        raise ValueError("unknown arm %r" % arm)
    a = lambda o, c=None: left.act(o, c)  # noqa: E731
    b = lambda o, c=None: right.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    if arm in ("A1", "A2"):
        cand_r = r0 if seat == 0 else r1
        base_r = r1 if seat == 0 else r0
        delta = cand_r - base_r
        winner = "A7" if delta > 0 else ("V3" if delta < 0 else "TIE")
    else:
        cand_r, base_r = r0, r1
        delta = r0 - r1
        winner = "SEAT0" if delta > 0 else ("SEAT1" if delta < 0 else "TIE")
    acts = [s[seat].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    if arm in ("A3", "A4"):
        acts1 = [s[1].get("action") for s in env.steps]
        digest1 = hashlib.sha256(json.dumps(acts1, sort_keys=True).encode()
                                 ).hexdigest()
    else:
        digest1 = None
    money = compact(env)
    money_digest = hashlib.sha256(json.dumps(money["money"]).encode()).hexdigest()
    state_digest = hashlib.sha256(json.dumps(money["struct12"]).encode()
                                 ).hexdigest()
    rec = {"key": "V29:%s:%d" % (arm, seed), "seed": seed, "arm": arm,
           "seat": seat, "cand": cand, "base": base,
           "cand_reward": cand_r, "base_reward": base_r,
           "seat0_reward": r0, "seat1_reward": r1, "delta": delta,
           "winner": winner, "tie_exact": delta == 0,
           "action_digest": digest, "action_digest_seat1": digest1,
           "money_digest": money_digest, "state_digest": state_digest,
           "engine_version": ENGINE_VERSION,
           "a7_digest": A7_FILE_SHA, "v3_digest": V3_SHA,
           "sim_digest": dict(SIM_DIGESTS),
           "harness_digest": harness_digest(),
           "config_fingerprint": config_fingerprint(),
           "cand_flags": dict(A7_FLAGS) if a7s else None,
           "step0_rewritten": [bool(x.step0_rewritten) for x in a7s] or None,
           "step0_unexpected_shape": [bool(x.step0_unexpected_shape)
                                      for x in a7s] or None,
           "pid": os.getpid(), "worker_nonce": WORKER_NONCE,
           "mode": spec.get("mode", "pool"),
           "timestamp": time.time(), "duration_sec": dur,
           "compact": money}
    return rec


def run_one_subprocess(seed, arm, timeout=900):
    """Run one match in a fully independent interpreter invocation."""
    code = (
        "import json,sys; sys.path.insert(0,%r); "
        "from v29_holdout_tournament import run_one, assert_frozen;"
        "assert_frozen();"
        "print(json.dumps(run_one({'seed':%d,'arm':%r,'mode':'fresh-subprocess'})))"
    ) % (os.path.join(REPO_ROOT, "scripts"), seed, arm)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, timeout=timeout, cwd=REPO_ROOT,
                       env=dict(os.environ))
    if p.returncode != 0:
        raise RuntimeError("subprocess match failed: %s" % p.stderr[-2000:])
    return json.loads(p.stdout.strip().splitlines()[-1])


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="340050:340089")
    ap.add_argument("--arms", default="A1,A2,A3,A4")
    ap.add_argument("--out", default="v29_raw_results.jsonl")
    ap.add_argument("--mode", default="pool", choices=["pool", "serial"])
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--fresh-subprocess", action="store_true")
    ap.add_argument("--allow-consumed-qual", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    assert arms and all(a in ARMS for a in arms), arms
    seeds = list(range(lo, hi + 1))
    for s in seeds:
        check_seed_allowed(s, args.allow_consumed_qual)
    out_path = (args.out if os.path.isabs(args.out) or os.sep in args.out
                else os.path.join(RESULTS, args.out))
    done = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["key"])
    queue = [{"seed": s, "arm": a, "mode": args.mode}
             for s in seeds for a in arms
             if "V29:%s:%d" % (a, s) not in done]
    print("v29 seeds=%d..%d arms=%s queued=%d done=%d mode=%s workers=%d fresh_subprocess=%s"
          % (lo, hi, ",".join(arms), len(queue), len(done), args.mode,
             args.workers, args.fresh_subprocess), flush=True)
    if not queue:
        return
    t_start = time.time()
    n = 0
    with open(out_path, "a", encoding="utf-8") as f_out:
        if args.fresh_subprocess:
            for spec in queue:
                rec = run_one_subprocess(spec["seed"], spec["arm"])
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
    print("v29 elapsed %.1fs wrote %d" % (time.time() - t_start, n), flush=True)
    recs = [json.loads(line) for line in open(out_path) if line.strip()]
    import statistics
    for arm in arms:
        ds = [r["delta"] for r in recs if r["arm"] == arm]
        if ds:
            print("arm=%s n=%d mean=%+.2f median=%+.1f min=%+.0f max=%+.0f" % (
                arm, len(ds), statistics.mean(ds), statistics.median(ds),
                min(ds), max(ds)))


if __name__ == "__main__":
    main()
