"""V31R2: exact fills + pool-at-sell. Settles timing-vs-size-vs-fills."""
import json, sys
from collections import Counter

def analyze(path):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index("Eldritch") if "Eldritch" in teams else 0
    steps = d["steps"]
    n = len(steps)
    money = [[st[i]["observation"]["farms"][st[i]["observation"]["player"]]["money"] for st in steps] for i in (0, 1)]
    print(f"##### ep{d['info'].get('EpisodeId')} {teams} final={[f'{x:.0f}' for x in d['rewards']]}")
    for i, tag in ((ours, "us"), (1 - ours, "op")):
        fills = Counter(); rev = 0.0; rev_steps = 0
        pool_px = []
        for t in range(n - 1):
            st = steps[t][i]
            mkt = st["action"].get("market", [])
            sells = [m for m in mkt if isinstance(m, list) and m and m[0] == "SELL" and len(m) >= 3]
            if not sells:
                continue
            shed = dict(st["observation"]["private"]["shed"])
            prices = st["observation"]["market"]["prices"]
            for m in sells:
                prod, qty = m[1], m[2]
                if not isinstance(prod, str) or not isinstance(qty, int):
                    continue
                f = min(qty, shed.get(prod, 0))
                fills[prod] += f
                shed[prod] = shed.get(prod, 0) - f
                pool_px.append(prices.get(prod, 0))
            ops = {m[0] for m in mkt if isinstance(m, list) and m}
            if not (ops - {"SELL"}):
                rev += money[i][t + 1] - money[i][t]
                rev_steps += 1
        tot_fill = sum(fills.values())
        print(f"  {tag}: filled_units={tot_fill} sellonly_rev={rev:.0f} over {rev_steps} steps "
              f"rev/fill={rev/tot_fill:.2f}")
        import statistics
        if pool_px:
            print(f"    pool-at-sell px: med={statistics.median(pool_px):.0f} mean={statistics.mean(pool_px):.0f}")
        print(f"    fills by prod: {dict(fills)}")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
