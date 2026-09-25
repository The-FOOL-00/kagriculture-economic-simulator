# SPDX-License-Identifier: MIT
"""V28 mechanism drill-down (diagnostic, frozen bytes).

Dumps divergent-step actions + money/position context for:
- 249530/s0 (typical +1286): unit@19, markets, t=251/252 jump
- 249542/s0 (+1369): same, contrast the +83
- 249534/s1 (+12087): expansion timeline (pasture/hands/cash)
- 249544/s0 (-3154): farm-route timeline
Writes results/v28_mechanism_detail.json + stdout summary.
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

OUT = os.path.join(REPO_ROOT, "results", "v28_mechanism_detail.json")


def run(seed, seat):
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: a7.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b] if seat == 0 else [b, a])
    return env


def farm(env, i, p):
    return env.steps[i][p]["observation"]["farms"][p]


def act(env, i, p):
    return env.steps[i][p].get("action") or {}


def counts(f):
    tiles = f.get("tiles", []) or []
    d = {}
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                d[t.get("kind")] = d.get(t.get("kind"), 0) + 1
    return d


def dump_typical(seed, seat):
    env = run(seed, seat)
    o = {"seed": seed, "seat": seat}
    # step-0 actions (the wash)
    o["step0_a7_market"] = act(env, 1, seat).get("market")
    o["step0_v3_market"] = act(env, 1, 1 - seat).get("market")
    o["step0_a7_farmer"] = act(env, 1, seat).get("farmer")
    o["step0_v3_farmer"] = act(env, 1, 1 - seat).get("farmer")
    # step-19 unit divergence (action index 19? env.steps[i] holds action taken at i-1)
    for i in range(1, 40):
        aa, ab = act(env, i, seat), act(env, i, 1 - seat)
        ua = [aa.get("farmer")] + list(aa.get("hands") or [])
        ub = [ab.get("farmer")] + list(ab.get("hands") or [])
        if ua != ub:
            o["unit_div"] = {"step": i, "a7": ua, "v3": ub,
                             "a7_pos": [farm(env, i - 1, seat).get("farmer")] +
                             list(farm(env, i - 1, seat).get("hands") or []),
                             "v3_pos": [farm(env, i - 1, 1 - seat).get("farmer")] +
                             list(farm(env, i - 1, 1 - seat).get("hands") or [])}
            break
    for i in range(1, len(env.steps)):
        if (act(env, i, seat).get("market") or []) != \
           (act(env, i, 1 - seat).get("market") or []):
            o.setdefault("mkt_divs", []).append(
                {"step": i, "a7": act(env, i, seat).get("market"),
                 "v3": act(env, i, 1 - seat).get("market")})
    # t=251/252 jump context
    for i in (250, 251, 252, 253):
        fA, fB = farm(env, i, seat), farm(env, i, 1 - seat)
        o.setdefault("jump", []).append(
            {"obs": i, "a7_money": fA.get("money"), "v3_money": fB.get("money"),
             "a7_shed": fA.get("shed"), "v3_shed": fB.get("shed")})
    o["tile_counts_end_a7"] = counts(farm(env, len(env.steps) - 1, seat))
    o["tile_counts_end_v3"] = counts(farm(env, len(env.steps) - 1, 1 - seat))
    return o


def dump_expansion(seed, seat):
    env = run(seed, seat)
    o = {"seed": seed, "seat": seat, "timeline": []}
    n = len(env.steps)
    for i in range(0, n, 12):
        row = {"obs": i}
        for p, tag in ((seat, "a7"), (1 - seat, "v3")):
            f = farm(env, i, p)
            tiles = f.get("tiles", []) or []
            past = sum(1 for r in tiles for t in r
                       if isinstance(t, dict) and t.get("kind") == "PASTURE")
            row[tag] = {"money": round(f.get("money", 0), 1),
                        "past": past,
                        "hands": len(f.get("hands", []) or []),
                        "quads": len(f.get("unlocked_quadrants", []) or [])}
        o["timeline"].append(row)
    # fine timeline around the seat1 investment dip (t≈380-450)
    o["fine"] = []
    for i in range(360, 470, 4):
        row = {"obs": i}
        for p, tag in ((seat, "a7"), (1 - seat, "v3")):
            f = farm(env, i, p)
            row[tag] = round(f.get("money", 0), 1)
        o["fine"].append(row)
    # market actions in the divergence window
    o["mkt_window"] = []
    for i in range(280, 470):
        aa = act(env, i, seat).get("market") or []
        ab = act(env, i, 1 - seat).get("market") or []
        buy = [x for x in aa + ab if x and x[0] in ("BUY_LAND", "BUY_ANIMAL", "HIRE")]
        if buy or aa != ab and i % 12 == 0:
            o["mkt_window"].append({"step": i, "a7": aa, "v3": ab})
    return o


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert_frozen()
    out = {"typical_249530": dump_typical(249530, 0),
           "plus83_249542": dump_typical(249542, 0),
           "tip_249534_s1": dump_expansion(249534, 1),
           "loss_249544_s0": dump_expansion(249544, 0)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    t = out["typical_249530"]
    print("TYPICAL step0 mkt:", t["step0_a7_market"], "vs", t["step0_v3_market"])
    print("TYPICAL step0 farmer:", t["step0_a7_farmer"], "vs", t["step0_v3_farmer"])
    print("TYPICAL unit_div:", json.dumps(t["unit_div"]))
    print("TYPICAL mkt_divs:", json.dumps(t["mkt_divs"]))
    print("TYPICAL jump:")
    for j in t["jump"]:
        print("  obs=%d a7=%.1f v3=%.1f" % (j["obs"], j["a7_money"], j["v3_money"]))
    print("TYPICAL a7 shed@250:", t["jump"][0]["a7_shed"])
    print("TYPICAL v3 shed@250:", t["jump"][0]["v3_shed"])
    print("TYPICAL end tiles a7:", t["tile_counts_end_a7"])
    print("TYPICAL end tiles v3:", t["tile_counts_end_v3"])
    e = out["plus83_249542"]
    print("1369 mkt_divs:", json.dumps(e["mkt_divs"]))
    print("1369 unit_div:", json.dumps(e["unit_div"]))
    print("1369 jump:", [(j["obs"], j["a7_money"], j["v3_money"]) for j in e["jump"]])


if __name__ == "__main__":
    main()
