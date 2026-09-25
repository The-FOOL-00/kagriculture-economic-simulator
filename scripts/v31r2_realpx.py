"""V31R2: realized-price estimator. Revenue on SELL-only steps / units ordered."""
import json, sys
from collections import Counter

BUY_OPS = {"BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND"}

def realized(path):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index("Eldritch") if "Eldritch" in teams else 0
    steps = d["steps"]
    n = len(steps)
    money = [[st[i]["observation"]["farms"][st[i]["observation"]["player"]]["money"] for st in steps] for i in (0, 1)]
    res = {}
    for i, tag in ((ours, "us"), (1 - ours, "op")):
        rev = Counter(); units = Counter(); rev_steps = 0
        for t in range(n - 1):
            mkt = steps[t][i]["action"].get("market", [])
            ops = {m[0] for m in mkt if isinstance(m, list) and m}
            if "SELL" in ops and not (ops & BUY_OPS):
                rev_steps += 1
                rev_units = Counter()
                for m in mkt:
                    if isinstance(m, list) and m and m[0] == "SELL" and len(m) >= 3 and isinstance(m[1], str):
                        rev_units[m[1]] += m[2]
                tot = sum(rev_units.values())
                if rev_units and tot > 0:
                    dm = money[i][t + 1] - money[i][t]
                    for p, u in rev_units.items():
                        rev[p] += dm * u / tot
                        units[p] += u
        res[tag] = {p: (rev[p] / units[p], units[p]) for p in units}
        res[tag + "_steps"] = rev_steps
    print(f"##### ep{d['info'].get('EpisodeId')} {teams} final={[f'{x:.0f}' for x in d['rewards']]}")
    prods = sorted(set(res["us"]) | set(res["op"]))
    print(f"  {'prod':12s} {'us_px':>8s} {'us_u':>7s} | {'op_px':>8s} {'op_u':>7s}")
    for p in prods:
        u = res["us"].get(p, (0, 0)); o = res["op"].get(p, (0, 0))
        print(f"  {p:12s} {u[0]:8.1f} {u[1]:7.0f} | {o[0]:8.1f} {o[1]:7.0f}")
    print(f"  sell-only steps: us={res['us_steps']} op={res['op_steps']}")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        realized(p)
