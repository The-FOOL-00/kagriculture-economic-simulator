"""V31R2 loss forensics extractor: compact per-replay timelines."""
import json, sys
from collections import Counter, defaultdict

OUR = "Eldritch"

def cell_kind(cell):
    if cell is None: return "EMPTY"
    if isinstance(cell, str): return cell
    k = cell.get("kind")
    if k == "PLANT": return "P_" + cell.get("crop", "?")
    if k == "ANIMAL": return "A_" + cell.get("animal", "?")
    return str(k)

def parse_market(mactions):
    """Aggregate one step's market action list."""
    agg = Counter()
    for a in mactions:
        if not a: continue
        op = a[0]
        if op in ("BUY_PRODUCT", "SELL") and len(a) >= 3:
            agg[(op, a[1])] += a[2]
        elif op in ("BUY_SEED", "BUY_ANIMAL") and len(a) >= 3:
            agg[(op, a[1])] += a[2]
        elif op in ("HIRE", "BUY_LAND", "FERTILIZE", "COLLECT", "SELL_ANIMAL"):
            agg[(op,)] += a[1] if len(a) > 1 and isinstance(a[1], int) else 1
        else:
            agg[(op,)] += 1
    return agg

def extract(path):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index(OUR)
    opp = 1 - ours
    steps = d["steps"]
    n = len(steps)
    out = {"episode": d["info"].get("EpisodeId"), "teams": teams, "ours": ours,
           "rewards": d["rewards"], "seed": d["info"].get("seed"), "nsteps": n,
           "money": [[], []], "hands": [[], []], "quads": [[], []],
           "mkt": [{}, {}], "wash1": [None, None],
           "tile_series": [], "shed_end": [None, None], "inv_end": [None, None]}
    mkt_tot = [Counter(), Counter()]
    for t, st in enumerate(steps):
        for i in (0, 1):
            s = st[i]
            o = s["observation"]
            farm = o["farms"][o["player"]]
            out["money"][i].append(farm["money"])
            out["hands"][i].append(len(farm["hands"]))
            out["quads"][i].append(len(farm["unlocked_quadrants"]))
            m = parse_market(s["action"].get("market", []))
            mkt_tot[i].update(m)
            if t == 1:
                out["wash1"][i] = s["action"].get("market", [])
        if t % 24 == 0 or t == n - 1:
            snap = {}
            for i in (0, 1):
                o = st[i]["observation"]
                farm = o["farms"][o["player"]]
                c = Counter()
                for row in farm["tiles"]:
                    for cell in row:
                        c[cell_kind(cell)] += 1
                snap[i] = dict(c)
            out["tile_series"].append({"step": t, "p0": snap[0], "p1": snap[1]})
    for i in (0, 1):
        out["mkt"][i] = {("|".join(map(str, k))): v for k, v in mkt_tot[i].items()}
        lo = steps[-1][i]["observation"]
        out["shed_end"][i] = dict(lo["private"]["shed"])
        out["inv_end"][i] = lo["market"]["inventory"] if isinstance(lo["market"].get("inventory"), dict) else lo["market"].get("inventory")
    mo, mp = out["money"][ours], out["money"][opp]
    out["diff"] = [a - b for a, b in zip(mo, mp)]
    return out

def money_str(m, idxs):
    return " ".join(f"{t}:{m[t]:.0f}" for t in idxs if t < len(m))

def brief(e):
    o, p = e["ours"], 1 - e["ours"]
    L = [f"ep{e['episode']} {e['teams'][o]}(us) vs {e['teams'][p]} rew={e['rewards'][o]:.0f}/{e['rewards'][p]:.0f} d={e['rewards'][o]-e['rewards'][p]:+.0f}"]
    L.append(f"  wash1 us={json.dumps(e['wash1'][o])} opp={json.dumps(e['wash1'][p])}")
    L.append(f"  money us : {money_str(e['money'][o],[1,2,17,18,24,48,96,252,400,600,719])}")
    L.append(f"  money opp: {money_str(e['money'][p],[1,2,17,18,24,48,96,252,600,719])}")
    df = e["diff"]
    L.append(f"  diff(us-opp): {money_str(df,[1,2,17,18,24,48,96,252,400,600,719])}")
    # earliest crossing of |diff|>500 after step 24
    cross = next((t for t in range(25, len(df)) if abs(df[t]) > 500), None)
    L.append(f"  first |diff|>500 after t24: step {cross} (diff={df[cross]:+.0f})" if cross else "  never |diff|>500 after t24")
    for i, tag in ((o, "us"), (p, "opp")):
        m = e["mkt"][i]
        hires = m.get("HIRE", 0)
        an = {k.split("|")[1]: v for k, v in m.items() if k.startswith("BUY_ANIMAL")}
        sd = {k.split("|")[1]: v for k, v in m.items() if k.startswith("BUY_SEED")}
        L.append(f"  {tag}: HIRE={hires} animals={an} seeds={sd} quads_end={e['quads'][i][-1]}")
        L.append(f"    tiles_end: {e['tile_series'][-1]['p0' if i==0 else 'p1']}")
    return "\n".join(L)

if __name__ == "__main__":
    for path in sys.argv[1:]:
        e = extract(path)
        print(brief(e))
        print()
