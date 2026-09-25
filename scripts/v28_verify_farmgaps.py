# SPDX-License-Identifier: MIT
"""V28 Phase 11 + tail-audit support.

1. Independent verification: re-run the preregistered 10-match subset
   (first 5 cohort seeds x 2 seats) in fully fresh subprocess
   interpreters; require exact reward+digest equality with the frozen
   tournament records.
2. Farm-gap controls: V3-vs-V3 (hermetic) on all 40 virgin seeds, one
   match per seed; gap = reward(seat0) - reward(seat1). Output
   results/v28_farm_gaps.jsonl. NEVER re-runs A7vV3 (no primary-record
   duplication risk).
"""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v28_confirmation_tournament import assert_frozen, run_one_subprocess  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RAW = os.path.join(REPO_ROOT, "results", "v28_raw_results.jsonl")
FARM = os.path.join(REPO_ROOT, "results", "v28_farm_gaps.jsonl")


def v3v3(seed):
    v0 = V3BackboneAdapter()
    v1 = V3BackboneAdapter()
    a = lambda o, c=None: v0.act(o, c)  # noqa: E731
    b = lambda o, c=None: v1.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    return {"seed": seed, "r0": r0, "r1": r1, "gap": r0 - r1,
            "pid": os.getpid()}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert_frozen()
    frozen = {r["key"]: r for l in open(RAW) for r in [json.loads(l)]}
    assert len(frozen) == 80

    # 1. Independent fresh-subprocess verification (prereg §8).
    print("== independent verification (10 matches) ==", flush=True)
    bad = 0
    for seed in range(249530, 249535):
        for seat in (0, 1):
            r = run_one_subprocess(seed, seat)
            f = frozen["V28:%d:%d" % (seed, seat)]
            ok = (r["cand_reward"], r["base_reward"], r["action_digest"],
                  r["money_digest"]) == \
                 (f["cand_reward"], f["base_reward"], f["action_digest"],
                  f["money_digest"])
            bad += not ok
            print("V28:%d:%d %s" % (seed, seat, "IDENTICAL" if ok else "*** DIFF ***"),
                  flush=True)
    assert bad == 0, "independent verification FAILED"
    print("independent verification: 10/10 IDENTICAL", flush=True)

    # 2. Farm gaps.
    print("== farm gaps (40 V3v3 matches) ==", flush=True)
    done = set()
    if os.path.exists(FARM):
        for line in open(FARM):
            if line.strip():
                done.add(json.loads(line)["seed"])
    queue = [s for s in range(249530, 249570) if s not in done]
    with open(FARM, "a", encoding="utf-8") as f_out:
        if queue:
            with ProcessPoolExecutor(max_workers=9,
                                     max_tasks_per_child=1) as ex:
                futs = {ex.submit(v3v3, s): s for s in queue}
                for fut in as_completed(futs):
                    f_out.write(json.dumps(fut.result()) + "\n")
                    f_out.flush()
    gaps = [json.loads(l) for l in open(FARM) if l.strip()]
    nz = [(g["seed"], g["gap"]) for g in gaps if g["gap"] != 0]
    print("farm gaps: %d/40 nonzero: %s" % (len(nz), nz), flush=True)


if __name__ == "__main__":
    main()
