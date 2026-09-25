"""V31R2: live scorecard analysis from summary.jsonl + leaderboard CSV."""
import csv, json, statistics
from collections import Counter, defaultdict
from glob import glob

LB = glob("live_data/episodes_v31r2/kaggriculture-publicleaderboard-*.csv")[0]
lb = {}
lbrate = {}
for r in csv.DictReader(open(LB, encoding="utf-8-sig")):
    lb[r["TeamName"]] = float(r["Score"])
    lbrate[r["TeamName"]] = int(r["Rank"])

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
rows = [r for r in seen.values() if r.get("type") != "EpisodeType.EPISODE_TYPE_VALIDATION"]

def report(sub):
    r = [x for x in rows if x["sub"] == sub]
    r.sort(key=lambda x: x["createTime"])
    c = Counter(x["result"] for x in r)
    w, l, t = c.get("W", 0), c.get("L", 0), c.get("T", 0)
    n = len(r)
    opp = [(lb.get(x["opp_team"], float("nan")), x["opp_team"], x["result"]) for x in r]
    known = [o for o in opp if o[0] == o[0]]
    print(f"===== {sub}: n={n} W={w} L={l} T={t} winrate={w/n:.3f} =====")
    if known:
        s = sorted(o[0] for o in known)
        print(f"  opp LB-score: n={len(known)} min={s[0]:.0f} p25={s[len(s)//4]:.0f} "
              f"med={statistics.median(s):.0f} mean={statistics.mean(s):.0f} p75={s[3*len(s)//4]:.0f} max={s[-1]:.0f}")
        for res in "WLT":
            ss = sorted(o[0] for o in known if o[2] == res)
            if ss:
                print(f"    vs {res}: n={len(ss)} opp_med={statistics.median(ss):.0f} opp_mean={statistics.mean(ss):.0f} opprange=[{ss[0]:.0f},{ss[-1]:.0f}]")
    ours = [x["our_reward"] for x in r]
    print(f"  our_reward: med={statistics.median(ours):.0f} mean={statistics.mean(ours):.0f} min={min(ours):.0f} max={max(ours):.0f}")
    d = [x["delta"] for x in r]
    print(f"  delta: med={statistics.median(d):.0f} mean={statistics.mean(d):.0f}")
    # losses by opponent
    print("  --- losses (opp, oppLB, delta) ---")
    for x in sorted([x for x in r if x["result"] == "L"], key=lambda x: x["delta"]):
        print(f"    ep{x['episode_id']} vs {x['opp_team']} (LB {lb.get(x['opp_team'],'?')}) delta={x['delta']:.0f} ours={x['our_reward']:.0f} opp={x['opp_reward']:.0f}")
    # wins vs strongest
    print("  --- top-10 wins by opp LB ---")
    wins = sorted([x for x in r if x["result"] == "W"], key=lambda x: lb.get(x["opp_team"], -1e9), reverse=True)[:10]
    for x in wins:
        print(f"    ep{x['episode_id']} vs {x['opp_team']} (LB {lb.get(x['opp_team'],'?')}) delta=+{x['delta']:.0f}")
    return r

a7 = report("a7")
v = report("v22r1")

# overlap
ao = defaultdict(list)
vo = defaultdict(list)
for x in a7:
    ao[x["opp_team"]].append(x["result"])
for x in v:
    vo[x["opp_team"]].append(x["result"])
shared = sorted(set(ao) & set(vo), key=lambda t: -lb.get(t, -1e9))
print(f"\n===== SHARED OPPONENTS: {len(shared)} =====")
for t in shared:
    print(f"  {t} (LB {lb.get(t,'?')} rk{lbrate.get(t,'?')}): A7={dict(Counter(ao[t]))} V22R1={dict(Counter(vo[t]))}")
