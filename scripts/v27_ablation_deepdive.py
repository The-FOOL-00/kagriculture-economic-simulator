# SPDX-License-Identifier: MIT
"""V27 ablation deep-dive: action-stream divergence across variants.

Full-capture recapture (adapter path) for:
  249431/seat0 x {P3, A1, A2, A3, A7, V3S} vs V3   (typical +1145 seed)
  249463/seat0 x {P3, A1, A3} vs V3               (tip seed)
Compares per-turn unit-verb streams and market streams pairwise
(first-diverging turn + money-gap series). Answers: do variants part
from V3 at step 1 (route/init) or late (reactive)?

Output: results/v27_ablation_deepdive.json (comparisons only).
"""

import json
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402
from v27_replay_trajectories import capture, fidelity_digest  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_ablation_deepdive.json")


def run_variant(variant, opp, seed, seat):
    if variant == "P3":
        var = V25P3BackboneAdapter()
    elif variant == "V3":
        var = V3BackboneAdapter()
    else:
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
    traj = capture(env, seat)
    return {"variant": variant, "opp": opp, "seed": seed, "seat": seat,
            "cand_reward": r0 if seat == 0 else r1,
            "base_reward": r1 if seat == 0 else r0,
            "delta": (r0 - r1) if seat == 0 else (r1 - r0),
            "action_digest": fidelity_digest(env, seat),
            "duration_sec": dur, "traj": traj}


def verb_stream(seat_traj, n):
    out = []
    for t in range(n):
        f = seat_traj["f_op"][t]
        out.append(((f[0] if f else "NONE"),
                    tuple((h[0] if h else "NONE") for h in (seat_traj["h_ops"][t] or []))))
    return out


def first_diff(a, b):
    for t, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return t
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cases = ([("P3", "V3", 249431, 0), ("V27-ABL-A1", "V3", 249431, 0),
              ("V27-ABL-A2", "V3", 249431, 0), ("V27-ABL-A3", "V3", 249431, 0),
              ("V27-ABL-A7", "V3", 249431, 0), ("V27-ABL-V3S", "V3", 249431, 0),
              ("P3", "V3", 249463, 0), ("V27-ABL-A1", "V3", 249463, 0),
              ("V27-ABL-A3", "V3", 249463, 0)])
    runs = {}
    for variant, opp, seed, seat in cases:
        key = "%s:%d:%d" % (variant, seed, seat)
        print("running %s ..." % key, flush=True)
        runs[key] = run_variant(variant, opp, seed, seat)
        r = runs[key]
        print("  delta=%+.0f digest=%s (%.1fs)" % (
            r["delta"], r["action_digest"][:12], r["duration_sec"]), flush=True)
    out = {"runs": {}, "comparisons": []}
    for key, r in runs.items():
        t = r["traj"]
        cs, bs = r["seat"], 1 - r["seat"]
        out["runs"][key] = {
            "delta": r["delta"], "digest": r["action_digest"],
            "money_gap": [round(t["seats"][cs]["money"][i] - t["seats"][bs]["money"][i], 1)
                          for i in range(0, 720, 12)],
        }
    # pairwise: candidate-verb streams + candidate-market streams
    keys431 = [k for k in runs if ":249431:" in k]
    for i in range(len(keys431)):
        for j in range(i + 1, len(keys431)):
            a, b = runs[keys431[i]], runs[keys431[j]]
            na = verb_stream(a["traj"]["seats"][a["seat"]], 719)
            nb = verb_stream(b["traj"]["seats"][b["seat"]], 719)
            ma = [json.dumps(m, sort_keys=True) for m in a["traj"]["seats"][a["seat"]]["market"][:719]]
            mb = [json.dumps(m, sort_keys=True) for m in b["traj"]["seats"][b["seat"]]["market"][:719]]
            out["comparisons"].append({
                "pair": [keys431[i], keys431[j]],
                "first_unit_diff": first_diff(na, nb),
                "first_market_diff": first_diff(ma, mb),
            })
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    for c in out["comparisons"]:
        print("%s vs %s: unit@%s market@%s" % (
            c["pair"][0].split(":")[0], c["pair"][1].split(":")[0],
            c["first_unit_diff"], c["first_market_diff"]))
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
