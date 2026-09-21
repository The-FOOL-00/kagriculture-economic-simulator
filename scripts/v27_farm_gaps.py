# SPDX-License-Identifier: MIT
"""V27: V3-vs-V3 farm-gap experiment (hermetic adapters).

On seeds where P3-vs-V3 seat mirrors disagree (e.g. 249450: +279/-5054),
the within-match contrast mixes program effects with farm/route
asymmetry. A V3-vs-V3 match on the same seed measures the PURE farm gap
G_s = V3@farm0 - V3@farm1 (same program, different farms).

Farm-purged program effects per seed:
  eps_s0 = Delta0 - G_s    (P3-vs-V3 at seat 0, minus farm gap)
  eps_s1 = Delta1 + G_s    (P3-vs-V3 at seat 1, minus farm gap)

60 seeds: A(249430..449) + B(249450..469) + C(249470..489).
Output: results/v27_farm_gaps.jsonl + console decomposition.
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_farm_gaps.jsonl")


def run_one(seed):
    a = V3BackboneAdapter()
    b = V3BackboneAdapter()
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([lambda o, c=None: a.act(o, c),
             lambda o, c=None: b.act(o, c)])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    return {"seed": seed, "v3_seat0": r0, "v3_seat1": r1,
            "farm_gap": r0 - r1, "duration_sec": dur}


def main():
    seeds = list(range(249430, 249450)) + list(range(249450, 249470)) + \
        list(range(249470, 249490))
    done = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["seed"])
    todo = [s for s in seeds if s not in done]
    print("queued=%d done=%d" % (len(todo), len(done)), flush=True)
    if todo:
        t_start = time.time()
        with open(OUT_PATH, "a", encoding="utf-8") as f_out:
            with ProcessPoolExecutor(max_workers=9) as ex:
                futs = {ex.submit(run_one, s): s for s in todo}
                n = 0
                for fut in as_completed(futs):
                    rec = fut.result()
                    f_out.write(json.dumps(rec) + "\n")
                    f_out.flush()
                    n += 1
                    if n % 20 == 0:
                        print("... %d/%d (%.0fs)" % (n, len(todo),
                                                    time.time() - t_start),
                              flush=True)
        print("elapsed %.1fs" % (time.time() - t_start), flush=True)

    # decomposition vs history-free P3-vs-V3 deltas
    gaps = {}
    with open(OUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                gaps[r["seed"]] = r["farm_gap"]
    led = [json.loads(l) for l in
           open(os.path.join(RESULTS, "v27_ledger.jsonl")) if l.strip()]
    p3 = [l for l in led if l["series"] in ("DISC-P3'", "CONF-P3'", "V26A1")]
    import collections
    by_seed = collections.defaultdict(dict)
    for l in p3:
        by_seed[l["seed"]][l["seat"]] = l["terminal_delta"]
    print("seed      D0       D1       G(V3v3)   eps0     eps1")
    e0, e1 = [], []
    for s in sorted(by_seed):
        d0, d1 = by_seed[s][0], by_seed[s][1]
        g = gaps[s]
        x0, x1 = d0 - g, d1 + g
        e0.append(x0)
        e1.append(x1)
        flag = "  <-- farm!" if abs(g) > 300 else ""
        print("%d  %+7.0f  %+7.0f  %+7.0f  %+7.0f  %+7.0f%s"
              % (s, d0, d1, g, x0, x1, flag))
    import statistics
    print("farm_gap: mean=%+.1f sd=%.1f max|.|=%.0f" % (
        statistics.mean(gaps.values()), statistics.stdev(gaps.values()),
        max(abs(g) for g in gaps.values())))
    print("eps0: mean=%+.1f sd=%.1f | eps1: mean=%+.1f sd=%.1f" % (
        statistics.mean(e0), statistics.stdev(e0),
        statistics.mean(e1), statistics.stdev(e1)))
    pooled = e0 + e1
    print("pooled farm-purged program effect: mean=%+.1f sd=%.1f n=%d" % (
        statistics.mean(pooled), statistics.stdev(pooled), len(pooled)))


if __name__ == "__main__":
    main()
