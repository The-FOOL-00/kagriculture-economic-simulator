# SPDX-License-Identifier: MIT
"""V27 Phase 3-4: behavioral delta ledger + first material divergence.

Reads trajectory records (fresh F2 series primary; hermetic V26A1;
harness series only for code validation / artifact forensics) and emits
one compact ledger record per P3-vs-V3 match.

Ledger contents per match:
  opening      : step-0 market orders, post-wash money, wash P&L
  capital      : money-gap series summaries, max drawdown, final gap
  market       : goods-cashflow (BUY/SELL x forward-filled price), event counts
  labor        : verb counts by phase, WATER/DIG gaps, PASS gaps
  crop         : plant/dry/weed gaps, shed wheat/milk gaps
  livestock    : pasture/cow/sheep trajectories, first-pasture step
  land         : quad unlock steps
  terminal     : final money/shed/inventory composition
  divergence   : first-crossing step per category + winning classification
  emergence    : first step the money gap locks onto the terminal sign

Category thresholds (material = economically meaningful, not tape noise):
  CAPITAL   |money gap| >= $250 held 12+ steps
  MARKET    |cumulative goods-cashflow gap| >= $250
  CROP      |plant-count gap| >= 4
  LABOR     |cumulative (WATER+DIG) gap| >= 10
  LIVESTOCK |pasture-animal gap| >= 1 or pasture-count gap >= 1
  LAND      |quads gap| >= 1
  ROUTE     |cumulative MOVE-count gap| >= 20
  TERMINAL  first crossing at step > 648
Classification = earliest crossing category (ties broken toward the
category with the largest terminal-normalized magnitude; all listed).

Caveat: within-match contrasts are cross-farm (P3@seat vs V3@1-seat), so
LEVEL gaps mix program effects with farm asymmetry. Seat-mirror symmetry
(per-seed gap correlation) separates the two; see report.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(REPO_ROOT, "results")
GOODS9 = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
          "MILK", "WOOL", "FERTILIZER"]

FRESH_PATH = os.path.join(RESULTS, "v27_fresh_trajectories.jsonl")
HARNESS_PATH = os.path.join(RESULTS, "v27_trajectories.jsonl")
LEDGER_PATH = os.path.join(RESULTS, "v27_ledger.jsonl")


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def verb_of(a):
    if isinstance(a, list) and a:
        return a[0]
    return "NONE"


def price_at(snaps, step):
    """Forward-filled goods prices for game step."""
    best = snaps[0]
    for s in snaps:
        if s["step"] <= step:
            best = s
        else:
            break
    return best["prices"]


def market_cashflow(market_actions, snaps):
    """Cumulative goods cashflow per step. HIRE/ANIMAL/SEED counted, not priced."""
    n = len(market_actions)
    cum = [0.0] * n
    run = 0.0
    counts = {"BUY_PRODUCT": 0, "SELL": 0, "HIRE": 0, "BUY_ANIMAL": 0,
              "BUY_SEED": 0, "OTHER": 0}
    events = []  # (step, op, good, qty, price)
    for t, orders in enumerate(market_actions):
        if orders:
            prices = price_at(snaps, t)
            for o in orders:
                if not isinstance(o, list) or not o:
                    continue
                op = o[0]
                if op == "BUY_PRODUCT" and len(o) >= 3:
                    g, q = o[1], o[2]
                    p = prices[GOODS9.index(g)] if g in GOODS9 else 0
                    run -= q * (p or 0)
                    counts["BUY_PRODUCT"] += 1
                    events.append((t, op, g, q, p))
                elif op == "SELL" and len(o) >= 3:
                    g, q = o[1], o[2]
                    p = prices[GOODS9.index(g)] if g in GOODS9 else 0
                    run += q * (p or 0)
                    counts["SELL"] += 1
                    events.append((t, op, g, q, p))
                elif op == "HIRE":
                    counts["HIRE"] += 1
                elif op == "BUY_ANIMAL":
                    counts["BUY_ANIMAL"] += 1
                elif op == "BUY_SEED":
                    counts["BUY_SEED"] += 1
                else:
                    counts["OTHER"] += 1
        cum[t] = run
    return cum, counts, events


def count_verbs(f_ops, h_ops_list, verbs):
    """Cumulative count of unit-actions whose verb is in `verbs`, per step."""
    n = len(f_ops)
    cum = [0] * n
    run = 0
    for t in range(n):
        if verb_of(f_ops[t]) in verbs:
            run += 1
        for h in (h_ops_list[t] or []):
            if verb_of(h) in verbs:
                run += 1
        cum[t] = run
    return cum


def first_persistent_crossing(gap, thresh, hold):
    """First t with |gap[t]|>=thresh and |gap|>=thresh/2.5 for hold+ steps after."""
    n = len(gap)
    for t in range(n):
        if abs(gap[t]) >= thresh:
            ok = True
            for k in range(1, hold + 1):
                if t + k >= n or abs(gap[t + k]) < thresh / 2.5:
                    ok = False
                    break
            if ok:
                return t
    return None


def first_crossing(gap, thresh):
    for t, g in enumerate(gap):
        if abs(g) >= thresh:
            return t
    return None


def ledger_one(rec):
    traj = rec["traj"]
    n = traj["n_steps"]
    seat = rec["seat"]
    cs, bs = seat, 1 - seat  # cand / base seats
    C, B = traj["seats"][cs], traj["seats"][bs]
    snaps = traj["market"]

    money_c, money_b = C["money"], B["money"]
    money_gap = [c - b for c, b in zip(money_c, money_b)]
    terminal = money_gap[-1]

    # opening
    wash_c = C["market"][0]
    wash_b = B["market"][0]
    opening = {
        "wash_c": wash_c, "wash_b": wash_b,
        "money1_c": money_c[1], "money1_b": money_b[1],
        "wash_pnl_c": money_c[1] - money_c[0],
        "wash_pnl_b": money_b[1] - money_b[0],
    }

    # market cashflow
    cum_c, cnt_c, ev_c = market_cashflow(C["market"], snaps)
    cum_b, cnt_b, ev_b = market_cashflow(B["market"], snaps)
    mkt_gap = [c - b for c, b in zip(cum_c, cum_b)]

    # labor
    chore_c = count_verbs(C["f_op"], C["h_ops"], {"WATER", "DIG"})
    chore_b = count_verbs(B["f_op"], B["h_ops"], {"WATER", "DIG"})
    pass_c = count_verbs(C["f_op"], C["h_ops"], {"PASS"})
    pass_b = count_verbs(B["f_op"], B["h_ops"], {"PASS"})
    move_c = count_verbs(C["f_op"], C["h_ops"], {"MOVE"})
    move_b = count_verbs(B["f_op"], B["h_ops"], {"MOVE"})
    harv_c = count_verbs(C["f_op"], C["h_ops"], {"HARVEST"})
    harv_b = count_verbs(B["f_op"], B["h_ops"], {"HARVEST"})
    chore_gap = [c - b for c, b in zip(chore_c, chore_b)]

    # crops / livestock / land gaps
    plant_gap = [c["plant"] - b["plant"] for c, b in zip(C["tiles"], B["tiles"])]
    dry_gap = [c["dry"] - b["dry"] for c, b in zip(C["tiles"], B["tiles"])]
    weed_gap = [c["weed"] - b["weed"] for c, b in zip(C["tiles"], B["tiles"])]
    past_gap = [c["pasture"] - b["pasture"] for c, b in zip(C["tiles"], B["tiles"])]
    animals = lambda T: T["cow"] + T["sheep"] + T["goose"]
    anim_gap = [animals(c) - animals(b) for c, b in zip(C["tiles"], B["tiles"])]
    quad_gap = [c - b for c, b in zip(C["quads_n"], B["quads_n"])]
    move_gap = [c - b for c, b in zip(move_c, move_b)]
    shed_wheat_gap = [c[0] - b[0] for c, b in zip(C["shed"], B["shed"])]
    shed_milk_gap = [c[6] - b[6] for c, b in zip(C["shed"], B["shed"])]
    seed_wheat_gap = [c[0] - b[0] for c, b in zip(C["seeds"], B["seeds"])]

    first_past_c = next((t for t in range(n) if C["tiles"][t]["pasture"] > 0), None)
    first_past_b = next((t for t in range(n) if B["tiles"][t]["pasture"] > 0), None)

    # first-divergence per category
    div = {
        "CAPITAL": first_persistent_crossing(money_gap, 250, 12),
        "MARKET": first_crossing(mkt_gap, 250),
        "CROP": first_crossing(plant_gap, 4),
        "LABOR": first_crossing(chore_gap, 10),
        "LIVESTOCK": first_crossing(anim_gap, 1),
        "LAND": first_crossing(quad_gap, 1),
        "ROUTE": first_crossing(move_gap, 20),
    }
    # LIVESTOCK via pasture-count gap if animal gap never crosses
    if div["LIVESTOCK"] is None:
        div["LIVESTOCK"] = first_crossing(past_gap, 1)
    dated = {k: v for k, v in div.items() if v is not None}
    if dated:
        t_min = min(dated.values())
        cands = [k for k, v in dated.items() if v == t_min]
        if len(cands) == 1:
            primary = cands[0]
        else:
            # tie-break: largest terminal-normalized magnitude at crossing+24
            def mag(k):
                t2 = min(n - 1, t_min + 24)
                series = {"CAPITAL": money_gap, "MARKET": mkt_gap,
                          "CROP": plant_gap, "LABOR": chore_gap,
                          "LIVESTOCK": anim_gap, "LAND": quad_gap,
                          "ROUTE": move_gap}[k]
                scale = {"CAPITAL": 250.0, "MARKET": 250.0, "CROP": 4.0,
                         "LABOR": 10.0, "LIVESTOCK": 1.0, "LAND": 1.0,
                         "ROUTE": 20.0}[k]
                return abs(series[t2]) / scale
            primary = max(cands, key=mag)
        if t_min > 648:
            primary = "TERMINAL"
    else:
        t_min, primary = None, ("TERMINAL" if terminal != 0 else "NONE")

    # emergence: first t where gap locks onto terminal sign at >=min(500, |terminal|/2)
    emergence = None
    if terminal != 0:
        need = min(500.0, abs(terminal) / 2.0)
        sgn = 1 if terminal > 0 else -1
        for t in range(n):
            if money_gap[t] * sgn >= need and all(
                    money_gap[k] * sgn >= 0 for k in range(t, n)):
                emergence = t
                break

    # phase verb summaries (early<=143, mid<=431, late>431)
    def phase_counts(f_ops, h_ops):
        out = {}
        for name, lo, hi in [("early", 0, 143), ("mid", 144, 431), ("late", 432, n - 1)]:
            d = {}
            for t in range(lo, min(hi + 1, n)):
                v = verb_of(f_ops[t])
                d[v] = d.get(v, 0) + 1
                for h in (h_ops[t] or []):
                    v = verb_of(h)
                    d[v] = d.get(v, 0) + 1
            out[name] = d
        return out

    return {
        "key": rec["key"], "series": rec["series"],
        "seed": rec["seed"], "seat": rec["seat"],
        "terminal_delta": rec["delta"],
        "cand_reward": rec["cand_reward"], "base_reward": rec["base_reward"],
        "opening": opening,
        "market_counts_c": cnt_c, "market_counts_b": cnt_b,
        "market_goods_pnl_c": cum_c[-1], "market_goods_pnl_b": cum_b[-1],
        "labor_totals": {
            "chore_c": chore_c[-1], "chore_b": chore_b[-1],
            "pass_c": pass_c[-1], "pass_b": pass_b[-1],
            "move_c": move_c[-1], "move_b": move_b[-1],
            "harvest_c": harv_c[-1], "harvest_b": harv_b[-1],
        },
        "verbs_c": phase_counts(C["f_op"], C["h_ops"]),
        "verbs_b": phase_counts(B["f_op"], B["h_ops"]),
        "first_pasture_c": first_past_c, "first_pasture_b": first_past_b,
        "final_c": {"money": money_c[-1], "shed": C["shed"][-1],
                    "seeds": C["seeds"][-1], "tiles": C["tiles"][-1],
                    "quads": C["quads_n"][-1], "hands": C["hands_n"][-1]},
        "final_b": {"money": money_b[-1], "shed": B["shed"][-1],
                    "seeds": B["seeds"][-1], "tiles": B["tiles"][-1],
                    "quads": B["quads_n"][-1], "hands": B["hands_n"][-1]},
        "divergence": div, "divergence_t": t_min, "divergence_primary": primary,
        "emergence_t": emergence,
        "gap_extremes": {"money_max": max(money_gap), "money_min": min(money_gap),
                         "mkt_max": max(mkt_gap), "mkt_min": min(mkt_gap),
                         "chore_final": chore_gap[-1],
                         "plant_final": plant_gap[-1],
                         "anim_final": anim_gap[-1],
                         "shed_wheat_final": shed_wheat_gap[-1],
                         "shed_milk_final": shed_milk_gap[-1]},
        "n_sell_events_c": sum(1 for e in ev_c if e[1] == "SELL"),
        "n_sell_events_b": sum(1 for e in ev_b if e[1] == "SELL"),
    }


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "fresh"
    if which == "fresh":
        recs = load_jsonl(FRESH_PATH)
        out_path = LEDGER_PATH
    elif which == "harness":
        recs = load_jsonl(HARNESS_PATH)
        out_path = os.path.join(RESULTS, "v27_ledger_harness.jsonl")
    elif which == "all":
        recs = load_jsonl(FRESH_PATH)
        recs += [r for r in load_jsonl(HARNESS_PATH) if r["series"] == "V26A1"]
        out_path = LEDGER_PATH
    else:
        raise SystemExit("usage: v27_ledger.py [fresh|harness|all]")
    print("ledger input: %d records from %s" % (len(recs), which), flush=True)
    ledgers = [ledger_one(r) for r in recs]
    with open(out_path, "w", encoding="utf-8") as f:
        for l in ledgers:
            f.write(json.dumps(l, sort_keys=True) + "\n")
    # summary
    import collections
    prim = collections.Counter(l["divergence_primary"] for l in ledgers)
    print("primary divergence:", dict(prim))
    em = [l["emergence_t"] for l in ledgers if l["emergence_t"] is not None]
    print("emergence: n=%d/%d median=%s" % (
        len(em), len(ledgers),
        sorted(em)[len(em) // 2] if em else None))
    print("wrote", out_path, flush=True)


if __name__ == "__main__":
    main()
