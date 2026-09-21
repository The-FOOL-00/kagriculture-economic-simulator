# SPDX-License-Identifier: MIT
"""V27 forensics: fresh-context replay to isolate worker-history effects.

V25's file loader lets candidates `import main` (the V3 payload) through the
process-global module cache, so a reused pool worker replays a STALE V3
module whose residue depends on which matches ran earlier in that worker.
The adapter loader (V26) is hermetic (fresh namespace per match).

Modes:
  F1  Queue-replay of the 40 CONF-P3 tasks in a fresh plain pool
      (V25 confirmation queue order, 9 workers, no trajectories).
      High fidelity => worker-history explains the harness mismatch.
  F2  History-free map: every V25 row (120 DISC + 40 CONF) replayed with
      maxtasksperchild=1 (exactly one match per OS process) WITH full
      trajectories. This is the TRUE frozen-program behavior series
      (A'/B') used by the V27 ledger.

Outputs:
  results/v27_f1_conf_replay.jsonl      (40 small records)
  results/v27_fresh_trajectories.jsonl  (160 trajectory records)
"""

import json
import multiprocessing as mp
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, REPO_ROOT)

from v27_replay_trajectories import (  # noqa: E402
    RESULTS, build_queue, fidelity_digest, run_file_match, v25_idle_rate,
    capture,
)

F1_OUT = os.path.join(RESULTS, "v27_f1_conf_replay.jsonl")
F2_OUT = os.path.join(RESULTS, "v27_fresh_trajectories.jsonl")


def f1_one(spec):
    env, dur = run_file_match(spec["seed"], spec["seat"], spec["cand_path"])
    seat = spec["seat"]
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    exp = spec["expect"]
    return {
        "series": spec["series"], "seed": spec["seed"], "seat": seat,
        "cand_reward": cand_r, "base_reward": base_r,
        "delta": cand_r - base_r,
        "action_digest": fidelity_digest(env, seat),
        "early_idle_rate": v25_idle_rate(env, seat),
        "duration_sec": dur,
        "digest_match": fidelity_digest(env, seat) == exp["digest"],
        "cand_match": cand_r == exp["cand"],
        "base_match": base_r == exp["base"],
    }


def f2_one(spec):
    env, dur = run_file_match(spec["seed"], spec["seat"], spec["cand_path"])
    seat = spec["seat"]
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    exp = spec["expect"]
    dg = fidelity_digest(env, seat)
    return {
        "series": spec["series"] + "'", "seed": spec["seed"], "seat": seat,
        "key": "%s':%d:%d" % (spec["series"], spec["seed"], spec["seat"]),
        "cand_reward": cand_r, "base_reward": base_r,
        "delta": cand_r - base_r,
        "action_digest": dg,
        "early_idle_rate": v25_idle_rate(env, seat),
        "duration_sec": dur,
        "expect": exp,
        "fidelity": {"cand_match": cand_r == exp["cand"],
                     "base_match": base_r == exp["base"],
                     "digest_match": dg == exp["digest"]},
        "traj": capture(env, seat),
    }


def run_pool(fn, queue, out_path, maxtasks):
    done_keys = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        done_keys.add((r["series"].rstrip("'"), r["seed"], r["seat"]))
                    except Exception:
                        pass
    todo = [q for q in queue
            if (q["series"], q["seed"], q["seat"]) not in done_keys]
    print("%s: queued=%d done=%d" % (out_path, len(todo), len(done_keys)), flush=True)
    if not todo:
        return
    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=9, maxtasksperchild=maxtasks) as pool:
        with open(out_path, "a", encoding="utf-8") as f_out:
            n = 0
            for rec in pool.imap_unordered(fn, todo):
                f_out.write(json.dumps(rec) + "\n")
                f_out.flush()
                n += 1
                if n % 20 == 0:
                    print("... %d/%d (%.0fs)" % (n, len(todo), time.time() - t0),
                          flush=True)
    print("%s finished in %.1fs" % (out_path, time.time() - t0), flush=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "F2"
    queue = build_queue()
    if mode == "F1":
        conf = [q for q in queue if q["series"] == "CONF-P3"]
        run_pool(f1_one, conf, F1_OUT, None)
        recs = [json.loads(l) for l in open(F1_OUT) if l.strip()]
        m = sum(1 for r in recs if r["digest_match"])
        print("F1 CONF queue-replay fidelity: %d/%d digests exact" % (m, len(recs)))
    elif mode == "F2":
        v25 = [q for q in queue if q["series"] != "V26A1"]
        run_pool(f2_one, v25, F2_OUT, 1)
        recs = [json.loads(l) for l in open(F2_OUT) if l.strip()]
        import collections
        tot = collections.Counter()
        ok = collections.Counter()
        for r in recs:
            tot[r["series"]] += 1
            ok[r["series"]] += 1 if r["fidelity"]["digest_match"] else 0
        print("F2 fresh-process fidelity vs checkpoints:",
              {k: "%d/%d" % (ok[k], tot[k]) for k in sorted(tot)})
    else:
        raise SystemExit("unknown mode %s" % mode)


if __name__ == "__main__":
    main()
