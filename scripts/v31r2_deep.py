"""V31R2: deep snapshot forensics — per-50-step production/economy comparison."""
import json, sys
sys.path.insert(0, "scripts")
from v31r2_forensics import extract, cell_kind
from collections import Counter

SNAPS = [1, 24, 72, 120, 168, 216, 252, 300, 360, 420, 480, 540, 600, 660, 719]

def deep(path):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index("Eldritch") if "Eldritch" in teams else 0
    opp = 1 - ours
    steps = d["steps"]
    cum_sell = [Counter(), Counter()]
    cum_buy = [Counter(), Counter()]
    print(f"##### ep{d['info'].get('EpisodeId')} us={teams[ours]} vs {teams[opp]} final={d['rewards'][ours]:.0f}/{d['rewards'][opp]:.0f}")
    for t in SNAPS:
        st = steps[t]
        row = [f"t={t:3d}"]
        for i, tag in ((ours, "us"), (opp, "op")):
            o = st[i]["observation"]
            farm = o["farms"][o["player"]]
            c = Counter(cell_kind(x) for r in farm["tiles"] for x in r)
            plants = {k[2:]: v for k, v in c.items() if k.startswith("P_")}
            anims = {k[2:]: v for k, v in c.items() if k.startswith("A_")}
            row.append(f"{tag}$={farm['money']:.0f} H={len(farm['hands'])} Q={len(farm['unlocked_quadrants'])} Pl={plants} An={anims}")
        print("  " + " | ".join(row))
    # cumulative market flows
    for i, tag in ((ours, "us"), (opp, "op")):
        sell = Counter(); buy = Counter(); seeds = Counter(); anim = Counter(); hires = 0
        for st in steps:
            for a in st[i]["action"].get("market", []):
                if not a: continue
                if a[0] == "SELL" and len(a) >= 3: sell[a[1]] += a[2]
                elif a[0] == "BUY_PRODUCT" and len(a) >= 3: buy[a[1]] += a[2]
                elif a[0] == "BUY_SEED" and len(a) >= 3: seeds[a[1]] += a[2]
                elif a[0] == "BUY_ANIMAL" and len(a) >= 3: anim[a[1]] += a[2]
                elif a[0] == "HIRE": hires += 1
        print(f"  {tag} cumSELL={dict(sell)} cumBUY={dict(buy)} seeds={dict(seeds)} anim={dict(anim)} HIRE={hires}")
        print(f"  {tag} shed_end={dict(steps[-1][i]['observation']['private']['shed'])}")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        deep(p)
