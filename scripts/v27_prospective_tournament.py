# SPDX-License-Identifier: MIT
"""V27 Phases 10/12: prospective P3-vs-V3 tournament (hermetic adapters).

Usage: v27_prospective_tournament.py {A|B}
  A: Stage A discovery      seeds 249490..249509 x seats 0/1 (40 matches)
  B: Stage B confirmation   seeds 249510..249529 x seats 0/1 (40 matches)

Frozen P3 vs frozen V3, hermetic adapters, no AEC, no tuning.
Checkpointed, resumable. Compact capture (full money series + 12-step
structural series + finals + digests) for emergence/seat/farm analysis.

Stage B must not run until the post-Stage-A freeze is recorded.
"""

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
STAGES = {
    "A": (list(range(249490, 249510)), "v27_discovery_matches.jsonl"),
    "B": (list(range(249510, 249530)), "v27_confirmation_matches.jsonl"),
}
P3_SHA = "13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    seed, seat = spec["seed"], spec["seat"]
    p3 = V25P3BackboneAdapter()
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: p3.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b] if seat == 0 else [b, a])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    acts = [s[seat].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    return {"stage": spec["stage"], "seed": seed, "seat": seat,
            "key": "%s:%d:%d" % (spec["stage"], seed, seat),
            "cand_reward": cand_r, "base_reward": base_r,
            "delta": cand_r - base_r, "action_digest": digest,
            "duration_sec": dur, "compact": compact(env)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    stage = sys.argv[1] if len(sys.argv) > 1 else None
    assert stage in STAGES, "usage: v27_prospective_tournament.py {A|B}"
    # frozen-code assertions (fail before touching seeds if drifted)
    assert sha256_file(os.path.join(REPO_ROOT, "candidates", "v25_p3_unified.py")) == P3_SHA
    assert sha256_file(os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")) == V3_SHA
    import kaggle_environments
    assert kaggle_environments.__version__ == "1.32.7", kaggle_environments.__version__
    seeds, fname = STAGES[stage]
    out_path = os.path.join(RESULTS, fname)
    done = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["key"])
    queue = [{"stage": stage, "seed": s, "seat": t}
             for s in seeds for t in (0, 1)
             if "%s:%d:%d" % (stage, s, t) not in done]
    print("stage=%s queued=%d done=%d" % (stage, len(queue), len(done)), flush=True)
    if not queue:
        return
    t_start = time.time()
    with open(out_path, "a", encoding="utf-8") as f_out:
        with ProcessPoolExecutor(max_workers=9) as ex:
            futs = {ex.submit(run_one, spec): spec for spec in queue}
            n = 0
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
    print("stage %s elapsed %.1fs" % (stage, time.time() - t_start), flush=True)
    # summary
    recs = [json.loads(l) for l in open(out_path) if l.strip()]
    import statistics
    ds = [r["delta"] for r in recs]
    print("n=%d mean=%+.2f median=%+.1f sd=%.1f min=%+.0f max=%+.0f" % (
        len(ds), statistics.mean(ds), statistics.median(ds),
        statistics.stdev(ds) if len(ds) > 1 else 0.0, min(ds), max(ds)))


if __name__ == "__main__":
    main()
