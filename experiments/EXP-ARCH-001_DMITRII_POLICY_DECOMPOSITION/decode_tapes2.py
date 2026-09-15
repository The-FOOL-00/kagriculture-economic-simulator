"""EXP-ARCH-001 decoder part 2: economic schedules (static analysis only)."""
import json, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "analysis")
TAPES = json.load(open("extracted_agents/dmitrii_lb2800/actions.json"))
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}  # 1.32.7 (cppsim)

def w(name, text):
    p = os.path.join(OUT, name)
    open(p, "w").write(text)
    print("wrote", p, len(text), "chars")

# ---- 06: PLANT + BUY_SEED schedules per strategy x day ----
lines = ["# Crop schedules: PLANT ops and BUY_SEED qty per strategy x day", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}: PLANT(day,crop)=count")
    for day in range(30):
        c = collections.Counter()
        for s in range(day * 24, min(day * 24 + 24, 719)):
            for cm in [t[s]["farmer"]] + list(t[s].get("hands") or []):
                if cm and cm[0] == "PLANT" and len(cm) > 1:
                    c[cm[1]] += 1
        if c:
            lines.append(f"  day{day:>2}: {dict(c)}")
    lines.append(f"## STRATEGY {i}: BUY_SEED steps (step: crop x qty)")
    ev = []
    for s, a in enumerate(t):
        for m in a.get("market") or []:
            if m and m[0] == "BUY_SEED":
                ev.append(f"{s}:{m[1]}x{m[2]}")
    lines.append("  " + " ".join(ev))
    lines.append("")
w("06_crop_schedules.md", "\n".join(lines) + "\n")

# ---- 07: animal + construction timeline ----
lines = ["# Animal & construction: BUY_ANIMAL/BUILD/PLACE-animal, FEED/CARE/CFERT per day", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}")
    ev = []
    for s, a in enumerate(t):
        for m in a.get("market") or []:
            if m and m[0] in ("BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT"):
                ev.append(f"{s}:{m[0]}-{m[1] if len(m)>1 else ''}x{m[2] if len(m)>2 else 1}")
    lines.append("  market: " + " ".join(ev))
    lines.append("  day: BUILD_COOP/BUILD_PASTURE/PLACE-animal/FEED/CARE/CFERT")
    for day in range(30):
        c = collections.Counter()
        for s in range(day * 24, min(day * 24 + 24, 719)):
            for cm in [t[s]["farmer"]] + list(t[s].get("hands") or []):
                if not cm:
                    continue
                if cm[0] in ("BUILD_COOP", "BUILD_PASTURE", "FEED", "CARE", "COLLECT_FERTILIZER"):
                    c[cm[0]] += 1
                elif cm[0] == "PLACE" and len(cm) > 1 and cm[1] in ("GOOSE", "COW", "SHEEP"):
                    c["PLACE_" + cm[1]] += 1
        if c:
            lines.append(f"  day{day:>2}: {dict(c)}")
    lines.append("")
w("07_animal_schedules.md", "\n".join(lines) + "\n")

# ---- 08: SELL cadence ----
lines = ["# SELL cadence: steps with SELL orders per strategy x product", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}")
    by = collections.defaultdict(list)
    for s, a in enumerate(t):
        for m in a.get("market") or []:
            if m and m[0] == "SELL":
                by[m[1]].append(f"{s}x{m[2]}")
    for p in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
        v = by.get(p, [])
        lines.append(f"  {p:<10} n={len(v):>3}: " + " ".join(v[:60]) + (" ..." if len(v) > 60 else ""))
    lines.append("")
w("08_sell_cadence.md", "\n".join(lines) + "\n")

# ---- 09: spend timeline (static price knowledge; SELL revenue unknowable statically) ----
def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
lines = ["# Daily deterministic spend per strategy (seeds+animals+hires+land; market-price buys/revenue excluded)", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}: day: seed$ anim$ hire$ land$ | cum")
    cum = 0
    for day in range(30):
        seed = anim = hire = land = 0; hires_today = 0
        for s in range(day * 24, min(day * 24 + 24, 719)):
            for m in t[s].get("market") or []:
                if not m:
                    continue
                if m[0] == "BUY_SEED":
                    seed += SEED_COST[m[1]] * m[2]
                elif m[0] == "BUY_ANIMAL":
                    anim += ANIMAL_COST[m[1]] * (m[2] if len(m) > 2 else 1)
                elif m[0] == "HIRE":
                    hire += fib(hires_today); hires_today += 1
                elif m[0] == "BUY_LAND":
                    land += 9999  # placeholder: depends on order NE/SW/SE
        cum += seed + anim + hire
        if seed or anim or hire or land:
            lines.append(f"  day{day:>2}: seed={seed:>5} anim={anim:>5} hire={hire:>4} land={'Y' if land else '-'} | cum~{cum}")
    lines.append("")
w("09_spend_timeline.md", "\n".join(lines) + "\n")

# ---- 10: hand-index role profiles ----
lines = ["# Worker-index op profiles (all steps, all strategies pooled + per-strategy animal-op share)", ""]
pool = collections.defaultdict(collections.Counter)
for i, t in enumerate(TAPES):
    for s, a in enumerate(t):
        pool["farmer"][a["farmer"][0] if a["farmer"] else "<EMPTY>"] += 1
        for hi, h in enumerate(a.get("hands") or []):
            pool[f"hand{hi}"][h[0] if h else "<EMPTY>"] += 1
for k in ["farmer"] + [f"hand{hi}" for hi in range(12)]:
    if k in pool:
        tot = sum(pool[k].values())
        top = pool[k].most_common(8)
        lines.append(f"{k}: n={tot} " + " ".join(f"{op}={c}" for op, c in top))
w("10_worker_roles.md", "\n".join(lines) + "\n")

# ---- 11: targeted diffs ----
lines = ["# Targeted tape diffs", ""]
def diffsteps(a, b, lo, hi):
    return [s for s in range(lo, hi + 1) if a[s] != b[s]]
lines.append("## tape0 vs tape2 over 144..647 (110 diffs): step list")
lines.append(json.dumps(diffsteps(TAPES[0], TAPES[2], 144, 647)))
lines.append("")
lines.append("## tape1 vs tape0 over 0..143 (dead-code diffs, never executed): step list")
dl = diffsteps(TAPES[1], TAPES[0], 0, 143)
lines.append(json.dumps(dl))
for s in dl:
    lines.append(f" step{s}: tape0={json.dumps(TAPES[0][s])[:300]}")
    lines.append(f" step{s}: tape1={json.dumps(TAPES[1][s])[:300]}")
lines.append("")
lines.append("## cluster micro-diffs over 144..647 (sample pairs)")
for a, b in [(1, 5), (1, 4), (7, 8), (3, 6), (1, 3), (4, 7), (10, 1), (11, 6)]:
    dl = diffsteps(TAPES[a], TAPES[b], 144, 647)
    lines.append(f"t{a} vs t{b}: {len(dl)} diffs: {dl[:40]}")
lines.append("")
lines.append("## outlier diffs: t9 vs t1, t12 vs t1 over 144..647 (first 30 steps)")
for a, b in [(9, 1), (12, 1), (9, 12)]:
    dl = diffsteps(TAPES[a], TAPES[b], 144, 647)
    lines.append(f"t{a} vs t{b}: {len(dl)} diffs, first30: {dl[:30]}")
w("11_targeted_diffs.md", "\n".join(lines) + "\n")

# ---- 12: workforce + HIRE timeline ----
lines = ["# Workforce: hands-list length per step (sampled) + HIRE counts per day", ""]
for i, t in enumerate(TAPES):
    hires = collections.Counter()
    for s, a in enumerate(t):
        for m in a.get("market") or []:
            if m and m[0] == "HIRE":
                hires[s // 24] += 1
    # hands length at hour 12 each day (mid-day, representative)
    wl = [(d, len(t[min(d * 24 + 12, 718)].get("hands") or [])) for d in range(30)]
    lines.append(f"## STRATEGY {i}")
    lines.append(f"  hands@midday per day: {wl}")
    lines.append(f"  hires/day: {dict(sorted(hires.items()))}")
w("12_workforce.md", "\n".join(lines) + "\n")
print("DONE")
