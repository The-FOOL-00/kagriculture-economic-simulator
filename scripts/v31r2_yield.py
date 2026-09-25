"""V31R2: harvested-yield audit v2 (tile-transition method).

yield[t+1] = yield[t] + growth - harvest - decay. HARVEST zeroes yield;
decay decrements by 1 past max_lifespan_step on even (step-mls).
Growth only via WATER (non-ongoing, same-step... actually WATER applies
during step t, visible in obs[t+1]) or daily ongoing/interval ticks.

Robust estimator: harvest[tile,t] = max(0, y[t]-y[t+1]-decay) when the
drop exceeds decay; attribute tile identity by (x,y,crop,planted_day).
This slightly misattributes WATER-growth (y rises) — but drops still
identify harvests since growth never decreases yield.
"""
import json, sys
from collections import Counter

def audit(path):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index("Eldritch") if "Eldritch" in teams else 0
    steps = d["steps"]
    n = len(steps)
    print(f"##### ep{d['info'].get('EpisodeId')} {teams} final={[f'{x:.0f}' for x in d['rewards']]}")
    for i, tag in ((ours, "us"), (1 - ours, "op")):
        tot = Counter(); events = 0
        for t in range(n - 1):
            fa = steps[t][i]["observation"]["farms"][steps[t][i]["observation"]["player"]]["tiles"]
            fb = steps[t + 1][i]["observation"]["farms"][steps[t + 1][i]["observation"]["player"]]["tiles"]
            for y in range(len(fa)):
                for x in range(len(fa[0])):
                    a, b = fa[y][x], fb[y][x]
                    if not (isinstance(a, dict) and a.get("kind") in ("PLANT",) or (isinstance(a, dict) and "animal" in a)):
                        continue
                    ya = a.get("yield_units", 0)
                    if ya <= 0:
                        continue
                    if not isinstance(b, dict):
                        # tile cleared (harvested non-ongoing) or replanted
                        tot[a.get("crop") or a.get("animal")] += ya
                        events += 1
                        continue
                    yb = b.get("yield_units", 0)
                    if yb < ya:
                        # possible decay: past lifespan, even steps
                        mls = a.get("max_lifespan_step", -1)
                        dec = 1 if (mls >= 0 and t + 1 >= mls and ((t + 1) - mls) % 2 == 0) else 0
                        h = ya - yb - dec
                        if h > 0:
                            tot[a.get("crop") or a.get("animal")] += h
                            events += 1
        print(f"  {tag}: harvest_events={events} yield={dict(tot)} total={sum(tot.values())}")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        audit(p)
