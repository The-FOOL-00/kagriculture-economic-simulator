"""EXP-ARCH-001 tape decoder (analysis only; not a performance experiment runner).

Reads extracted_agents/dmitrii_lb2800/actions.json and router_parent.py SHOP_PLANS,
writes human-readable summaries under this directory's analysis/ folder.
Does NOT touch frozen artifacts, DOES NOT submit to Kaggle, runs no sim matches.
"""
import json, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "analysis")
os.makedirs(OUT, exist_ok=True)
TAPES = json.load(open("extracted_agents/dmitrii_lb2800/actions.json"))

def w(name, text):
    p = os.path.join(OUT, name)
    open(p, "w").write(text)
    print("wrote", p, len(text), "chars")

# ---- 1. tape similarity structure ----
lines = ["# Tape structural similarity", ""]
# Are steps 0..143 identical across all 13 tapes?
def steps_equal(a, b, lo, hi):
    diffs = [s for s in range(lo, hi + 1) if a[s] != b[s]]
    return diffs
base = TAPES[0]
lines.append("## steps 0..143 vs tape 0 (branch point check)")
for i in range(13):
    d = steps_equal(base, TAPES[i], 0, 143)
    lines.append(f"tape{i}: {len(d)} diffs" + (f" first@{d[:5]}" if d else " IDENTICAL"))
lines.append("")
lines.append("## steps 144..647 vs tape 0 (count diffs)")
for i in range(13):
    d = steps_equal(base, TAPES[i], 144, 647)
    lines.append(f"tape{i}: {len(d)} diffs of 504")
lines.append("")
lines.append("## steps 648..718 vs tape 2 (forced plan-2 regime)")
for i in range(13):
    d = steps_equal(TAPES[2], TAPES[i], 648, 718)
    lines.append(f"tape{i}: {len(d)} diffs" + (f" first@{d[:5]}" if d else " IDENTICAL"))
lines.append("")
# pairwise diff counts over 144..647
lines.append("## pairwise diff counts over steps 144..647")
hdr = "     " + "".join(f"{i:>6}" for i in range(13))
lines.append(hdr)
for i in range(13):
    row = f"t{i:>3} " + "".join(f"{len(steps_equal(TAPES[i], TAPES[j], 144, 647)):>6}" for j in range(13))
    lines.append(row)
lines.append("")
# where in 144..647 do diffs concentrate? per-48-step blocks, # of distinct actions across tapes
lines.append("## distinct-action counts per 24-step day across 13 tapes (divergence map)")
for day in range(30):
    lo, hi = day * 24, min(day * 24 + 23, 718)
    distinct = len({json.dumps(TAPES[i][s], sort_keys=True) for i in range(13) for s in range(lo, hi + 1)})
    lines.append(f"day{day:>2} steps{lo:>3}..{hi:>3}: {distinct:>4} distinct of {13*24}")
w("01_tape_similarity.md", "\n".join(lines) + "\n")

# ---- 2. per-strategy market event timeline ----
lines = ["# Market event timelines per strategy", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}")
    for step, a in enumerate(t):
        m = a.get("market") or []
        if m:
            lines.append(f"  step{step:>3} d{step//24:>2}h{step%24:>2}: " + "; ".join(json.dumps(o) for o in m))
    lines.append("")
w("02_market_timelines.md", "\n".join(lines) + "\n")

# ---- 3. per-strategy per-day unit-op aggregates ----
lines = ["# Per-day unit-op aggregates (farmer+hands)", ""]
for i, t in enumerate(TAPES):
    lines.append(f"## STRATEGY {i}")
    for day in range(30):
        c = collections.Counter(); plants = collections.Counter(); handsmax = 0
        for s in range(day * 24, min(day * 24 + 24, 719)):
            a = t[s]
            cmds = [a["farmer"]] + list(a.get("hands") or [])
            handsmax = max(handsmax, len(a.get("hands") or []))
            for cm in cmds:
                if not cm:
                    c["<EMPTY>"] += 1; continue
                c[cm[0]] += 1
                if cm[0] == "PLANT" and len(cm) > 1:
                    plants[cm[1]] += 1
        mv = c.get("NORTH", 0) + c.get("SOUTH", 0) + c.get("EAST", 0) + c.get("WEST", 0)
        lines.append(f"  day{day:>2} hands<={handsmax:>2} move={mv:>3} PLANT={dict(plants) or '-'} "
                     f"WATER={c.get('WATER',0)} HARV={c.get('HARVEST',0)} FEED={c.get('FEED',0)} CARE={c.get('CARE',0)} "
                     f"CFERT={c.get('COLLECT_FERTILIZER',0)} FERT={c.get('FERTILIZE',0)} DIG={c.get('DIG',0)} "
                     f"COOP={c.get('BUILD_COOP',0)} PAST={c.get('BUILD_PASTURE',0)} PICK={c.get('PICKUP',0)} "
                     f"PLACE={c.get('PLACE',0)} DROP={c.get('DROP',0)} PASS={c.get('PASS',0)}")
    lines.append("")
w("03_daily_unit_ops.md", "\n".join(lines) + "\n")

# ---- 4. first-event table + investment totals ----
lines = ["# First events and investment totals per strategy", ""]
for i, t in enumerate(TAPES):
    first = {}
    seed_qty = collections.Counter(); anim_qty = collections.Counter()
    prod_qty = collections.Counter(); hires = 0; land = 0
    sell_first = {}
    for step, a in enumerate(t):
        for m in a.get("market") or []:
            if not m:
                continue
            op = m[0]
            if op == "HIRE":
                hires += 1; first.setdefault("HIRE", step)
            elif op == "BUY_SEED":
                seed_qty[m[1]] += m[2] if len(m) > 2 else 1
                first.setdefault(f"SEED_{m[1]}", step)
            elif op == "BUY_ANIMAL":
                anim_qty[m[1]] += m[2] if len(m) > 2 else 1
                first.setdefault(f"ANIMAL_{m[1]}", step)
            elif op == "BUY_PRODUCT":
                prod_qty[m[1]] += m[2] if len(m) > 2 else 1
                first.setdefault(f"PROD_{m[1]}", step)
            elif op == "BUY_LAND":
                land += 1; first.setdefault("LAND", step)
            elif op == "SELL":
                sell_first.setdefault(m[1], step)
    # workforce size over time (hands length)
    wf = [(s, len(t[s].get("hands") or [])) for s in (0, 72, 143, 144, 216, 288, 360, 432, 504, 576, 648, 700, 718)]
    lines.append(f"## STRATEGY {i}")
    lines.append(f"  first: {json.dumps(first, sort_keys=True)}")
    lines.append(f"  seed_qty: {dict(seed_qty)} anim_qty: {dict(anim_qty)} prod_qty: {dict(prod_qty)} hires={hires} land={land}")
    lines.append(f"  sell_first: {json.dumps({k: v for k, v in sorted(sell_first.items(), key=lambda kv: kv[1])})}")
    lines.append(f"  workforce(hands)@{wf}")
    lines.append("")
w("04_first_events.md", "\n".join(lines) + "\n")

# ---- 5. guards check: tape2 steps 712..717 must be 9-product SELL>=100; empty-order locations ----
lines = ["# Guard compatibility checks", ""]
prods = {"WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER"}
for s in range(712, 718):
    m = TAPES[2][s]["market"]
    ok = isinstance(m, list) and len(m) == 9 and all(isinstance(o, list) and len(o) == 3 and o[0] == "SELL" and o[1] in prods and isinstance(o[2], int) and o[2] >= 100 for o in m) and {o[1] for o in m} == prods
    lines.append(f"tape2 step{s}: fixed_market_ok={ok} n_orders={len(m)}")
    if not ok:
        lines.append("   " + json.dumps(m)[:400])
lines.append("")
empt = [(i, s) for i in range(13) for s in range(719) for o in (TAPES[i][s].get("market") or []) if not o]
lines.append(f"empty [] market orders total={len(empt)}")
bys = collections.Counter(i for i, s in empt)
lines.append("per strategy: " + json.dumps(dict(sorted(bys.items()))))
lines.append("in tape2 712..717: " + json.dumps([(i, s) for i, s in empt if i == 2 and 712 <= s <= 717]))
w("05_guard_checks.md", "\n".join(lines) + "\n")
print("DONE")
