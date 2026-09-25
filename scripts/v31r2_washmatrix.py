"""V31R2: wash-size payoff matrix. Attribute opp wash by team, tabulate by (sub, wash)."""
import json, statistics
from collections import defaultdict

tw = json.load(open("live_data/episodes_v31r2/team_wash_map.json"))
MIXED = {t for t, c in tw.items() if len(c) > 1}

def short(w):
    import re
    ops = re.findall(r'\["(BUY_PRODUCT|SELL|BUY_SEED|BUY_ANIMAL|HIRE)[^\]]*?\]', w)
    nums = re.findall(r'"(WHEAT|MELON|COW|SHEEP|GOOSE)", (\d+)', w)
    parts = []
    for m in __import__("re").finditer(r'\["([A-Z_]+)"(?:, "([A-Z]+)")?(?:, (\d+))?\]', w):
        op, item, n = m.groups()
        parts.append(f"{op[:3]}:{item or ''}{n or ''}")
    return "+".join(parts) if parts else w[:60]

seen = {}
for p in ["live_data/episodes_v31r2/summary.jsonl", "live_data/episodes_v31r2/sum0.jsonl",
          "live_data/episodes_v31r2/sum1.jsonl", "live_data/episodes_v31r2/sum2.jsonl",
          "live_data/episodes_v31r2/sum3.jsonl"]:
    try:
        for l in open(p):
            r = json.loads(l)
            if "error" not in r:
                seen[r["episode_id"]] = r
    except FileNotFoundError:
        pass

mat = defaultdict(list)  # (sub, wash) -> [(result, delta, team, ep)]
unatt = defaultdict(list)
for r in seen.values():
    if r.get("type") == "EpisodeType.EPISODE_TYPE_VALIDATION" or r["opp_team"] == "Eldritch":
        continue
    t = r["opp_team"]
    if t in tw and t not in MIXED:
        w = short(next(iter(tw[t])))
        mat[(r["sub"], w)].append((r["result"], r["delta"], t, r["episode_id"]))
    else:
        unatt[r["sub"]].append((r["result"], r["delta"], t, r["episode_id"]))

print("===== WASH MATRIX (rows: sub x opp_wash) =====")
for key in sorted(mat, key=lambda k: (k[0], -len(mat[k]))):
    v = mat[key]
    w = sum(1 for x in v if x[0] == "W")
    l = sum(1 for x in v if x[0] == "L")
    ds = sorted(x[1] for x in v)
    print(f"{key[0]:6s} vs {key[1]:44s} n={len(v):3d} W={w:3d} L={l:3d} "
          f"med={statistics.median(ds):+7.0f} mean={statistics.mean(ds):+7.0f} min={ds[0]:+7.0f} max={ds[-1]:+7.0f}")
print()
print("===== UNATTRIBUTED (opp team wash unseen) =====")
for sub in ("a7", "v22r1"):
    v = unatt[sub]
    w = sum(1 for x in v if x[0] == "W")
    print(f"{sub}: n={len(v)} W={w} L={len(v)-w}")
    for res, d, t, ep in sorted(v, key=lambda x: x[1]):
        print(f"   {res} {d:+8.0f} ep{ep} {t[:34]}")
