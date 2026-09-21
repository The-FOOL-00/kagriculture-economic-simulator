# SPDX-License-Identifier: MIT
"""V27 Phase 8: ablation tournament (exploratory, consumed seeds only).

Configs (120 matches each = 60 seeds x 2 seats):
  primary (vs V3 common baseline): ABL-A1/A2/A3/V3S vs V3
  secondary (direct, same game):   ABL-A1/A2/A3 vs P3
Hermetic adapters throughout. Compact capture (~15KB/match): full money
series + 12-step structural series + finals + digests + market counts.
Firewall: seeds 249430..249489 ONLY (consumed). Never 249490+.

V3S-vs-V3 must reproduce v27_farm_gaps.jsonl 60/60 exactly (sanity gate).
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
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_ablation_matches.jsonl")

SEEDS = list(range(249430, 249450)) + list(range(249450, 249470)) + \
    list(range(249470, 249490))
VARIANTS = ("V27-ABL-A1", "V27-ABL-A2", "V27-ABL-A3", "V27-ABL-V3S")
CONFIGS = ([(v, "V3") for v in VARIANTS] +
           [(v, "P3") for v in VARIANTS[:3]] +
           [("V27-ABL-A7", "V3"), ("V27-ABL-A7", "P3")])


def compact(env, seat):
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
    variant, opp, seed, seat = (spec["variant"], spec["opp"], spec["seed"],
                                spec["seat"])
    var = V27AblationAdapter(variant)
    base = V3BackboneAdapter() if opp == "V3" else V25P3BackboneAdapter()
    va = lambda o, c=None: var.act(o, c)  # noqa: E731
    ba = lambda o, c=None: base.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([va, ba] if seat == 0 else [ba, va])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    acts = [s[seat].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    return {
        "config": "%s-vs-%s" % (variant, opp),
        "variant": variant, "opp": opp, "seed": seed, "seat": seat,
        "key": "%s-vs-%s:%d:%d" % (variant, opp, seed, seat),
        "cand_reward": cand_r, "base_reward": base_r,
        "delta": cand_r - base_r,
        "action_digest": digest,
        "duration_sec": dur,
        "compact": compact(env, seat),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    done = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["key"])
    queue = []
    for variant, opp in CONFIGS:
        for seed in SEEDS:
            for seat in (0, 1):
                key = "%s-vs-%s:%d:%d" % (variant, opp, seed, seat)
                if key not in done:
                    queue.append({"variant": variant, "opp": opp,
                                  "seed": seed, "seat": seat})
    print("queued=%d done=%d" % (len(queue), len(done)), flush=True)
    if queue:
        t_start = time.time()
        with open(OUT_PATH, "a", encoding="utf-8") as f_out:
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
                    if n % 60 == 0:
                        print("... %d/%d (%.0fs)" % (n, len(queue),
                                                    time.time() - t_start),
                              flush=True)
        print("elapsed %.1fs" % (time.time() - t_start), flush=True)

    # sanity gate: V3S-vs-V3 must equal V3v3 farm gaps 60/60 exactly
    gaps = {}
    with open(os.path.join(RESULTS, "v27_farm_gaps.jsonl"), "r",
              encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                gaps[r["seed"]] = (r["v3_seat0"], r["v3_seat1"])
    n_ok = n_tot = 0
    with open(OUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["config"] != "V27-ABL-V3S-vs-V3":
                continue
            n_tot += 1
            e0, e1 = gaps[r["seed"]]
            if r["cand_reward"] == (e0 if r["seat"] == 0 else e1) and \
               r["base_reward"] == (e1 if r["seat"] == 0 else e0):
                n_ok += 1
            else:
                print("SANITY-DIFF seed=%d seat=%d got=%s/%s want=%s/%s"
                      % (r["seed"], r["seat"], r["cand_reward"],
                         r["base_reward"],
                         e0 if r["seat"] == 0 else e1,
                         e1 if r["seat"] == 0 else e0))
    print("V3S sanity gate: %d/%d exact vs farm gaps" % (n_ok, n_tot),
          flush=True)


if __name__ == "__main__":
    main()
