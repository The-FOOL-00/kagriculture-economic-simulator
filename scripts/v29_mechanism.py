# SPDX-License-Identifier: MIT
"""V29 Phase 12: mechanism replication telemetry (diagnostic re-execution).

Replays ALL 80 A7vV3 holdout legs (fresh adapters per leg, frozen bytes)
and records the 7 preregistered telemetry fields per leg
(V29_PREREGISTRATION.md s12) plus structural diagnostics. Writes
results/v29_mechanism.json + results/v29_mechanism.csv (one evidence row
per leg) and prints the classification + contribution table.

Action schema (verified on consumed seed 249431 before first holdout
use): market orders are [OP, ITEM, QTY] lists, e.g.
["BUY_SEED","MELON",2]; unit actions are ["PLANT","MELON"] / ["PASS"] /
["WATER"] etc. Game-step t action lives at env.steps[t+1]; obs[t] money
at env.steps[t][p]["observation"]["farms"][p]["money"].
"""

import csv
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v29_holdout_tournament import assert_frozen  # noqa: E402
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RAW = os.path.join(REPO_ROOT, "results", "v29_raw_results.jsonl")
OUT_JSON = os.path.join(REPO_ROOT, "results", "v29_mechanism.json")
OUT_CSV = os.path.join(REPO_ROOT, "results", "v29_mechanism.csv")
SEEDS = list(range(340050, 340090))


def units_of(action):
    return [action.get("farmer")] + list(action.get("hands") or [])


def melon_seed_qty(market):
    q = 0
    for o in market or []:
        if (isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "BUY_SEED"
                and o[1] == "MELON"):
            try:
                q += int(o[2])
            except (TypeError, ValueError):
                pass
    return q


def is_plant_melon(u):
    return (isinstance(u, (list, tuple)) and len(u) >= 2 and u[0] == "PLANT"
            and u[1] == "MELON")


def has_order(market, op, item=None):
    for o in market or []:
        if isinstance(o, (list, tuple)) and o and o[0] == op and \
           (item is None or (len(o) > 1 and o[1] == item)):
            return True
    return False


def struct_of(farm):
    tiles = farm.get("tiles", []) or []
    plant = past = 0
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    plant += 1
                elif t.get("kind") == "PASTURE":
                    past += 1
    return {"hands": len(farm.get("hands", []) or []), "plant": plant,
            "past": past,
            "quads": len(farm.get("unlocked_quadrants", []) or [])}


def analyze(seed, seat):
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: a7.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b] if seat == 0 else [b, a])
    n = len(env.steps)
    opp = 1 - seat

    def money(i, p):
        return env.steps[i][p]["observation"]["farms"][p].get("money", 0.0)

    def mkt(t, p):
        return (env.steps[t + 1][p].get("action") or {}).get("market") or []

    def units(t, p):
        return units_of(env.steps[t + 1][p].get("action") or {})

    # (1) step-17 cash gap
    cash17_gap = money(17, seat) - money(17, opp)
    # (2) melon-seed qty gap at step 17
    ms_gap = melon_seed_qty(mkt(17, seat)) - melon_seed_qty(mkt(17, opp))
    # (3) melon-plant action gap, full game
    pa = sum(1 for t in range(n - 1) for u in units(t, seat) if is_plant_melon(u))
    pb = sum(1 for t in range(n - 1) for u in units(t, opp) if is_plant_melon(u))
    # (4)/(5) divergence anatomy (t>=1; step-0 wash differs by construction)
    first_unit, first_mkt, n_unit, n_mkt = None, None, 0, 0
    for t in range(1, n - 1):
        if units(t, seat) != units(t, opp):
            n_unit += 1
            if first_unit is None:
                first_unit = t
        if mkt(t, seat) != mkt(t, opp):
            n_mkt += 1
            if first_mkt is None:
                first_mkt = t
    # (6) harvest jump: largest single-step money-gap increase, obs[100..400]
    gaps = [money(i, seat) - money(i, opp) for i in range(n)]
    hj_step, hj_size = None, 0.0
    for i in range(100, min(400, n)):
        d = gaps[i] - gaps[i - 1]
        if d > hj_size:
            hj_size, hj_step = d, i
    # (7) terminal delta
    delta = env.steps[-1][seat]["reward"] - env.steps[-1][opp]["reward"]
    # structural diagnostics
    end_a = struct_of(env.steps[n - 1][seat]["observation"]["farms"][seat])
    end_b = struct_of(env.steps[n - 1][opp]["observation"]["farms"][opp])
    a7_lands = sum(1 for t in range(n - 1) if has_order(mkt(t, seat), "BUY_LAND"))
    v3_lands = sum(1 for t in range(n - 1) if has_order(mkt(t, opp), "BUY_LAND"))
    return {"seed": seed, "seat": seat, "cash17_gap": cash17_gap,
            "melonseed17_gap": ms_gap, "plant_melon_gap": pa - pb,
            "plant_melon_a7": pa, "plant_melon_v3": pb,
            "first_unit_div": first_unit, "n_unit_div": n_unit,
            "first_mkt_div": first_mkt, "n_mkt_div": n_mkt,
            "harvest_step": hj_step, "harvest_jump": hj_size,
            "terminal_delta": delta,
            "end_a7": end_a, "end_v3": end_b,
            "pasture_gap": end_a["past"] - end_b["past"],
            "a7_buy_land": a7_lands, "v3_buy_land": v3_lands}


def classify(row, farm_gap_for_a7):
    """Mechanical classifier (preregistered class list, s12).

    farm_gap_for_a7: V3vV3 cash of A7's farm minus V3's farm (same seed).
    """
    d = row["terminal_delta"]
    if d == 0:
        return "TIE-INERT"
    if d > 0:
        if (row["melonseed17_gap"] >= 1 and row["plant_melon_gap"] == 1
                and 800 <= row["harvest_jump"] <= 1800
                and row["harvest_step"] is not None
                and 150 <= row["harvest_step"] <= 350):
            return "CANONICAL_MELON"
        if (d > 5000 and (row["pasture_gap"] >= 4 or row["a7_buy_land"] > row["v3_buy_land"])):
            return "SHEEP_GATE"
        return "OTHER_POSITIVE"
    if farm_gap_for_a7 is not None and farm_gap_for_a7 < -2000 and \
       (row["melonseed17_gap"] >= 1 or row["plant_melon_gap"] >= 1):
        return "FARM-ROUTE_LOSS"
    return "OTHER_NEGATIVE"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert_frozen()
    raw = [json.loads(l) for l in open(RAW) if l.strip()]
    a4 = {r["seed"]: r for r in raw if r["arm"] == "A4"}
    out = []
    for s in SEEDS:
        for seat in (0, 1):
            row = analyze(s, seat)
            v = a4[s]
            fg = (v["seat0_reward"] - v["seat1_reward"]) if seat == 0 else \
                (v["seat1_reward"] - v["seat0_reward"])
            row["farm_gap_for_a7"] = fg
            row["class"] = classify(row, fg)
            out.append(row)
            print("seed=%d seat=%d d=%+.0f cash17=%+.0f ms_gap=%d plant_gap=%d "
                  "udiv=%s/%d mdiv=%s/%d hj=%s/%+.0f class=%s"
                  % (s, seat, row["terminal_delta"], row["cash17_gap"],
                     row["melonseed17_gap"], row["plant_melon_gap"],
                     row["first_unit_div"], row["n_unit_div"],
                     row["first_mkt_div"], row["n_mkt_div"],
                     row["harvest_step"], row["harvest_jump"], row["class"]),
                  flush=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=[
            "seed", "seat", "terminal_delta", "class", "cash17_gap",
            "melonseed17_gap", "plant_melon_gap", "first_unit_div",
            "n_unit_div", "first_mkt_div", "n_mkt_div", "harvest_step",
            "harvest_jump", "pasture_gap", "farm_gap_for_a7"])
        wr.writeheader()
        for r in out:
            wr.writerow({k: r[k] for k in wr.fieldnames})
    from collections import Counter
    c = Counter(r["class"] for r in out)
    print("CLASSES:", dict(c))
    contrib = {}
    for r in out:
        contrib[r["class"]] = contrib.get(r["class"], 0.0) + r["terminal_delta"]
    print("CONTRIB:", {k: round(v, 1) for k, v in contrib.items()})
    canon = sum(1 for r in out if r["class"] == "CANONICAL_MELON")
    wins = sum(1 for r in out if r["terminal_delta"] > 0)
    print("canonical share of legs: %d/80; of wins: %d/%d" % (canon, canon, wins))


if __name__ == "__main__":
    main()
