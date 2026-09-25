# SPDX-License-Identifier: MIT
"""V28 mechanism audit probes (diagnostic re-execution, frozen bytes).

Writes results/v28_mechanism.json:
- exact gap-transition step on typical seeds (t=140..260 money gaps)
- per-step action-stream comparison A7-vs-V3 within each game:
  first unit divergence, first market divergence, counts
- structural series (hands/plant/pasture/quads) for tip/loss seeds
Seeds: 249530 (typical), 249542 (1369), 249533/249534/249544 (asym).
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v28_confirmation_tournament import assert_frozen  # noqa: E402
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

OUT = os.path.join(REPO_ROOT, "results", "v28_mechanism.json")
TARGETS = [(249530, 0), (249542, 0), (249533, 0), (249533, 1),
           (249534, 0), (249534, 1), (249544, 0), (249544, 1)]


def units_of(action):
    return [action.get("farmer")] + list(action.get("hands") or [])


def run(seed, seat):
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: a7.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b] if seat == 0 else [b, a])
    n = len(env.steps)
    gaps, first_unit_div, first_mkt_div = [], None, None
    unit_divs, mkt_divs = 0, 0
    for i in range(n):
        fa = env.steps[i][seat]["observation"]["farms"][seat]
        fb = env.steps[i][1 - seat]["observation"]["farms"][1 - seat]
        gaps.append(fa.get("money", 0.0) - fb.get("money", 0.0))
        aa = env.steps[i][seat].get("action") or {}
        ab = env.steps[i][1 - seat].get("action") or {}
        if i == 0:
            continue  # placeholder step
        if units_of(aa) != units_of(ab):
            unit_divs += 1
            if first_unit_div is None:
                first_unit_div = i
        if (aa.get("market") or []) != (ab.get("market") or []):
            mkt_divs += 1
            if first_mkt_div is None:
                first_mkt_div = i
    # structural endpoints + transition window
    struct = {}
    for s, tag in ((seat, "a7"), (1 - seat, "v3")):
        f0 = env.steps[0][s]["observation"]["farms"][s]
        fN = env.steps[-1][s]["observation"]["farms"][s]
        struct[tag] = {"hands_end": len(fN.get("hands", []) or []),
                       "quads_end": len(fN.get("unlocked_quadrants", []) or []),
                       "money_end": fN.get("money", 0.0)}
    # pasture counts end
    for s, tag in ((seat, "a7"), (1 - seat, "v3")):
        tiles = env.steps[-1][s]["observation"]["farms"][s].get("tiles", []) or []
        past = sum(1 for row in tiles for t in row
                   if isinstance(t, dict) and t.get("kind") == "PASTURE")
        struct[tag]["pasture_end"] = past
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    return {"seed": seed, "seat": seat,
            "delta": (r0 if seat == 0 else r1) - (r1 if seat == 0 else r0),
            "gap_window_140_260": [round(g, 2) for g in gaps[140:261]],
            "gap_t1": gaps[1], "gap_t24": gaps[24],
            "first_unit_div": first_unit_div, "unit_divs": unit_divs,
            "first_mkt_div": first_mkt_div, "mkt_divs": mkt_divs,
            "struct": struct, "n_steps": n}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert_frozen()
    out = [run(s, t) for s, t in TARGETS]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f)
    for r in out:
        print("seed=%d seat=%d delta=%+.0f unitdiv_first=%s/%d mktdiv_first=%s/%d "
              "past(a7/v3)=%d/%d hands=%d/%d quads=%d/%d" % (
                  r["seed"], r["seat"], r["delta"], r["first_unit_div"],
                  r["unit_divs"], r["first_mkt_div"], r["mkt_divs"],
                  r["struct"]["a7"]["pasture_end"],
                  r["struct"]["v3"]["pasture_end"],
                  r["struct"]["a7"]["hands_end"],
                  r["struct"]["v3"]["hands_end"],
                  r["struct"]["a7"]["quads_end"],
                  r["struct"]["v3"]["quads_end"]), flush=True)
    # transition step on typical seed
    w = out[0]["gap_window_140_260"]
    for i, g in enumerate(w):
        if abs(g - 28.0) > 1:
            print("typical 249530: gap leaves +28 at obs-step %d (gap=%s)"
                  % (140 + i, g))
            break
    for i, g in enumerate(w):
        if abs(g - 1286.0) < 1:
            print("typical 249530: gap reaches +1286 at obs-step %d"
                  % (140 + i))
            break


if __name__ == "__main__":
    main()
