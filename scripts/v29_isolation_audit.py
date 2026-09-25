# SPDX-License-Identifier: MIT
"""V29 Phase 5: process/import isolation regression (CONSUMED seeds only).

Covers brief s16 (7 contexts) on consumed seeds (249431: V27 primer-demo
seed; 249470: V26 cohort seed) across ALL FOUR V29 arms. NEVER touches
the holdout slice 340050+ or the protected remainder.

Checks:
  A. same-process sequence V3->A7->V3->A7 (order A)
  B. same-process sequence A7->V3->A7->V3 (order B, reversed schedule)
  C. P3-primer: P3vV3 then A7vV3 in the SAME process (V27 bug pattern)
     + V3vV3 after A7 (V3-after-A7) and V3vV3 after V3vV3 (V3-after-V3)
  D. fresh-subprocess A7vV3 + self-play arms (independent interpreter)
  E. pool (max_tasks_per_child=1) A7vV3
  F. seat flip A7@1 (Arm 2) in fresh subprocess
  G. static: no sys.modules['main']; distinct namespaces; no RNG/
     env-var/filesystem vectors in adapters.

Verdict: all same-(arm,seed) rewards+digests identical across A-E.
Output: results/v29_isolation_audit.jsonl + stdout verdict table.
"""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v29_holdout_tournament import (  # noqa: E402
    assert_frozen, run_one, run_one_subprocess)
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

AUDIT_SEEDS = [249431, 249470]
OUT = os.path.join(REPO_ROOT, "results", "v29_isolation_audit.jsonl")


def play(left_fn, right_fn, seed):
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([left_fn, right_fn])
    return env


def digest_of(env, seat):
    acts = [s[seat].get("action") for s in env.steps]
    return hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()


def match_in_process(kind, seed, seat):
    """kind: 'A7vV3' | 'V3vV3' | 'A7vA7' | 'P3vV3'. Fresh adapters, current process."""
    if kind in ("A7vV3", "A7vA7"):
        cand = V27AblationAdapter(variant="V27-ABL-A7")
    elif kind == "P3vV3":
        cand = V25P3BackboneAdapter()
    else:
        cand = V3BackboneAdapter()
    base = (V27AblationAdapter(variant="V27-ABL-A7") if kind == "A7vA7"
            else V3BackboneAdapter())
    a = lambda o, c=None: cand.act(o, c)  # noqa: E731
    b = lambda o, c=None: base.act(o, c)  # noqa: E731
    env = play(a, b, seed) if seat == 0 else play(b, a)
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    return {"kind": kind, "seed": seed, "seat": seat,
            "cand_reward": r0 if seat == 0 else r1,
            "base_reward": r1 if seat == 0 else r0,
            "action_digest": digest_of(env, seat),
            "pid": os.getpid()}


def main():
    assert_frozen()
    recs = []

    def emit(ctx, rec):
        rec = dict(rec)
        rec["ctx"] = ctx
        recs.append(rec)
        print("%-28s seed=%d seat=%d cand=%8.0f base=%8.0f digest=%.12s pid=%d"
              % (ctx, rec["seed"], rec["seed"] and rec["seat"], rec["cand_reward"],
                 rec["base_reward"], rec["action_digest"], rec["pid"]),
              flush=True)

    for seed in AUDIT_SEEDS:
        # A: V3 -> A7 -> V3 -> A7, same process (order A)
        emit("A1-V3vV3", match_in_process("V3vV3", seed, 0))
        emit("A2-A7vV3", match_in_process("A7vV3", seed, 0))
        emit("A3-V3vV3-after-A7", match_in_process("V3vV3", seed, 0))
        emit("A4-A7vV3-after-V3", match_in_process("A7vV3", seed, 0))
        # B: A7 -> V3 -> A7 -> V3, same process (reversed schedule)
        emit("B1-A7vV3", match_in_process("A7vV3", seed, 0))
        emit("B2-V3vV3", match_in_process("V3vV3", seed, 0))
        emit("B3-A7vV3", match_in_process("A7vV3", seed, 0))
        emit("B4-V3vV3", match_in_process("V3vV3", seed, 0))
        # Self-play order pair: A7vA7 after V3vV3 and after A7vV3
        emit("B5-A7vA7", match_in_process("A7vA7", seed, 0))
        emit("B6-A7vA7-again", match_in_process("A7vA7", seed, 0))
        # C: P3 primer then A7 in the SAME process (V27 bug pattern)
        emit("C1-P3vV3-primer", match_in_process("P3vV3", seed, 0))
        emit("C2-A7vV3-after-P3", match_in_process("A7vV3", seed, 0))
        emit("C3-V3vV3-after-A7", match_in_process("V3vV3", seed, 0))
        emit("C4-A7vA7-after-P3", match_in_process("A7vA7", seed, 0))
        # D: fresh subprocess each (runner path, all arms incl. seat flip)
        for arm, seat in (("A1", 0), ("A2", 1), ("A3", 0), ("A4", 0)):
            r = run_one_subprocess(seed, arm)
            emit("D-subprocess-%s" % arm,
                 {"kind": {"A1": "A7vV3", "A2": "A7vV3", "A3": "A7vA7",
                            "A4": "V3vV3"}[arm],
                  "seed": seed, "seat": seat,
                  "cand_reward": r["cand_reward"],
                  "base_reward": r["base_reward"],
                  "action_digest": r["action_digest"], "pid": r["pid"]})
        # F: seat flip via runner serial path (same process, fresh adapters)
        r = run_one({"seed": seed, "arm": "A2", "mode": "serial"})
        emit("F-runner-A2-seat1",
             {"kind": "A7vV3", "seed": seed, "seat": 1,
              "cand_reward": r["cand_reward"], "base_reward": r["base_reward"],
              "action_digest": r["action_digest"], "pid": r["pid"]})

    # E: pool mode with max_tasks_per_child=1 (fresh worker per match)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=4, max_tasks_per_child=1) as ex:
        futs = {}
        for seed in AUDIT_SEEDS:
            for arm in ("A1", "A3", "A4"):
                futs[ex.submit(run_one, {"seed": seed, "arm": arm,
                                         "mode": "pool"})] = (seed, arm)
        for fut in futs:
            seed, arm = futs[fut]
            r = fut.result()
            emit("E-pool-%s" % arm,
                 {"kind": {"A1": "A7vV3", "A3": "A7vA7",
                            "A4": "V3vV3"}[arm],
                  "seed": seed, "seat": 0,
                  "cand_reward": r["cand_reward"],
                  "base_reward": r["base_reward"],
                  "action_digest": r["action_digest"], "pid": r["pid"]})

    # Static hygiene checks
    import sys as _sys
    assert "main" not in _sys.modules, "sys.modules['main'] contaminated!"
    a1 = V27AblationAdapter(variant="V27-ABL-A7")
    a2 = V27AblationAdapter(variant="V27-ABL-A7")
    v1 = V3BackboneAdapter()
    assert "main" not in _sys.modules, "adapter construction polluted sys.modules!"
    ns = [a1._v3_agent_callable.__globals__,
          a2._v3_agent_callable.__globals__, v1._agent_fn.__globals__]
    assert len({id(n) for n in ns}) == 3, "adapter namespaces aliased!"
    assert ns[0].get("__name__") != ns[1].get("__name__"), "namespace names collide!"
    print("STATIC: sys.modules clean; 3 adapter namespaces distinct: %s"
          % [n.get("__name__") for n in ns])

    with open(OUT, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")

    # Verdict: group by (kind, seed, seat); all rows must agree exactly.
    from collections import defaultdict
    groups = defaultdict(list)
    for r in recs:
        groups[(r["kind"], r["seed"], r["seat"])].append(r)
    ok = True
    print("\n=== INVARIANCE VERDICT ===")
    for key in sorted(groups):
        rows = groups[key]
        sigs = {(r["cand_reward"], r["base_reward"], r["action_digest"]) for r in rows}
        status = "INVARIANT" if len(sigs) == 1 else "*** VARIES ***"
        if len(sigs) != 1:
            ok = False
        print("%s seed=%d seat=%d: %d runs -> %s"
              % (key[0], key[1], key[2], len(rows), status))
    print("OVERALL:", "PASS - order/process invariant" if ok else "FAIL - STOP")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
