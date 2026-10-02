#!/usr/bin/env python3
"""V58 in-simulator trajectory capture (committed).

Runs each executable elite agent vs V49 on discovery seeds, both seats, on the
authoritative engine (kaggle-environments 1.32.7), and records:
  - georgymamarin-compatible features (same definitions as features.py)
  - stream hashes with the SAME normalization (canonical JSON, NUL-joined,
    steps[0] skipped, 8 cuts) for direct comparison with S3 hash families
  - extended V58 features: daily animals/crops/crew/money/land, market action
    census, first-sale days, canonical action stream (for re-hash + forensics)

Output: research/v58/analysis/trajectories/<agent>_vs_v49_seed<seed>_p<seat>.json
        research/v58/analysis/trajectories/_capture_index.json
Seeds: 10000, 10001 (discovery split; never reused for fresh validation).
"""
import hashlib
import json
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRAJ = os.path.join(REPO, "research", "v58", "analysis", "trajectories")

AGENTS = {
    "v49": "candidates/v49_meta_fusion/main.py",
    "v44": "candidates/v44_economic_portfolio/main.py",
    "kaitofukami_v48_3009": "research/v47/elite_corpus/agents/kaitofukami_v48_3009/main.py",
    "saiteja_mega_3000": "research/v47/elite_corpus/agents/saiteja_mega_3000/main.py",
    "thomastschinkel_2945": "research/v47/elite_corpus/agents/thomastschinkel_2945/main.py",
    "tetsutani_pasture": "research/v47/elite_corpus/agents/tetsutani_pasture/main.py",
    "indarkarhana_top10": "research/v47/elite_corpus/agents/indarkarhana_top10/main.py",
    "dmitrii_lb2800": "extracted_agents/dmitrii_lb2800/main.py",
    "P3090_claimed": "external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py",
    "P3000_claimed": "external_repos/lixingtao123-Kaggriculture/opponents/public_3000/main.py",
    "night_harvest": "external_repos/lixingtao123-Kaggriculture/opponents/night_harvest/main.py",
}
V49 = AGENTS["v49"]
SEEDS = [10000, 10001]
CUTS = (24, 48, 100, 136, 200, 300, 400, 719)
CROPS = {"CARROT", "MELON", "STRAWBERRY", "TOMATO", "WHEAT"}

sys.stdout.reconfigure(line_buffering=True)


def cell_kind(cell):
    try:
        get = getattr(cell, "get", None)
        if get is None:
            return None, None
        kind = get("kind")
        if kind == "PLANT":
            return "PLANT", get("crop")
        if kind == "PASTURE":
            return "PASTURE", get("animal")
        return kind, None
    except Exception:  # noqa: BLE001
        return None, None


def canon(action):
    return json.dumps(action or {}, sort_keys=True, separators=(",", ":"))


def run_game(agent_name, agent_path, opp_path, seed, seat_of_agent):
    """Seat 0 = agent if seat_of_agent==0 else opponent. Returns record dict."""
    os.chdir(REPO)
    sys.path.insert(0, REPO)
    from kaggle_environments import make  # noqa: E402

    if seat_of_agent == 0:
        pair = [agent_path, opp_path]
    else:
        pair = [opp_path, agent_path]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(pair)
    steps = env.steps
    n = len(steps)

    prices = {}
    per_seat = []
    for seat in (0, 1):
        crops, first_land, peak_crew, hires_by_day = {}, None, 0, {}
        money, h = [], hashlib.sha256()
        hashes, streams = {}, []
        mkt_census, first_sale, sale_qty = {}, {}, {}
        daily = []
        for t, step in enumerate(steps):
            entry = step[seat]
            obs = entry["observation"]
            farm = obs["farms"][seat]
            day = t // 24
            m = farm["money"]
            money.append(m)
            try:
                hb = farm["hires_today"]
            except Exception:  # noqa: BLE001
                hb = 0
            hires_by_day[day] = max(hires_by_day.get(day, 0), hb or 0)
            try:
                crew = len(farm["hands"])
            except Exception:  # noqa: BLE001
                crew = 0
            peak_crew = max(peak_crew, crew)
            a = entry.get("action") or {}
            if t:  # skip steps[0] per stream-hash convention
                s = canon(a)
                streams.append(s)
                h.update(s.encode())
                h.update(b"\0")
                if t in CUTS:
                    hashes[f"stream_h{t}"] = h.hexdigest()[:16]
            for order in (a.get("market") or []):
                if isinstance(order, list) and order:
                    op = order[0]
                    mkt_census[op] = mkt_census.get(op, 0) + 1
                    if op == "BUY_LAND" and first_land is None:
                        first_land = day
                    if op == "SELL" and len(order) > 1:
                        prod = order[1]
                        if prod not in first_sale:
                            first_sale[prod] = day
                        try:
                            sale_qty[prod] = sale_qty.get(prod, 0) + int(order[2])
                        except Exception:  # noqa: BLE001
                            pass
            for unit in [a.get("farmer") or []] + list(a.get("hands") or []):
                if isinstance(unit, list) and unit and unit[0] == "PLANT" and len(unit) > 1 \
                        and unit[1] in CROPS:
                    crops[unit[1]] = crops.get(unit[1], 0) + 1
            if t % 24 == 23 or t == n - 1:  # end-of-day snapshot
                animals, plants = {}, {}
                try:
                    for row in farm["tiles"]:
                        for cell in row:
                            k, v = cell_kind(cell)
                            if k == "PASTURE" and v:
                                animals[v] = animals.get(v, 0) + 1
                            elif k == "PLANT" and v:
                                plants[v] = plants.get(v, 0) + 1
                except Exception:  # noqa: BLE001
                    pass
                try:
                    quads = list(farm["unlocked_quadrants"] or [])
                except Exception:  # noqa: BLE001
                    quads = []
                daily.append({"day": day, "money": m, "crew": crew,
                              "animals": animals, "plants": plants, "quads": quads})
        for prod, price in steps[0][seat]["observation"]["market"]["prices"].items():
            pass
        # prices shared: summarize once (do after loop to avoid duplication)
        per_seat.append({"crops": crops, "first_land": first_land, "peak_crew": peak_crew,
                         "hires_by_day": hires_by_day, "money": money, "hashes": hashes,
                         "streams": streams, "mkt_census": mkt_census,
                         "first_sale": first_sale, "sale_qty": sale_qty, "daily": daily})
    for s in steps:
        for prod, price in s[0]["observation"]["market"]["prices"].items():
            lo, hi = prices.get(prod, (price, price))
            prices[prod] = (min(lo, price), max(hi, price))
    fin = steps[-1]
    out = {"agent": agent_name, "opp": "v49" if agent_path != opp_path else agent_name,
           "seed": seed, "seat": seat_of_agent, "steps": n,
           "rewards": [float(fin[0].reward or 0), float(fin[1].reward or 0)],
           "statuses": [str(fin[0].status), str(fin[1].status)],
           "prices": {p: [lo, hi] for p, (lo, hi) in sorted(prices.items())},
           "seats": []}
    for seat in (0, 1):
        ps = per_seat[seat]
        money = ps["money"]
        final = money[-1] if money else 0
        elbow = None
        if final and final > 0:
            cross = next((t for t, v in enumerate(money) if v > final * 0.1), None)
            elbow = None if cross is None else cross // 24
        out["seats"].append({
            "is_agent": seat == seat_of_agent,
            "geo_features": {
                "final_money": final, "peak_crew": ps["peak_crew"],
                "total_hires": sum(ps["hires_by_day"].values()),
                "first_land_day": ps["first_land"], "elbow_day": elbow,
                "tiles_planted": sum(ps["crops"].values()),
                **{f"plants_{c.lower()}": ps["crops"].get(c, 0) for c in
                   ["CARROT", "MELON", "STRAWBERRY", "TOMATO", "WHEAT"]}},
            "hashes": ps["hashes"],
            "mkt_census": ps["mkt_census"], "first_sale": ps["first_sale"],
            "sale_qty": ps["sale_qty"], "daily": ps["daily"],
            "streams": ps["streams"],
        })
    return out


def task(args):
    name, path, seed, seat = args
    try:
        rec = run_game(name, os.path.join(REPO, path), os.path.join(REPO, V49), seed, seat)
        fn = f"{name}_vs_v49_seed{seed}_p{seat}.json"
        with open(os.path.join(TRAJ, fn), "w") as f:
            json.dump(rec, f)
        r = rec["rewards"]
        mine = r[seat]
        opp = r[1 - seat]
        return {"task": fn, "ok": True, "mine": mine, "opp": opp,
                "win": mine > opp, "statuses": rec["statuses"]}
    except Exception:  # noqa: BLE001
        return {"task": f"{name}_vs_v49_seed{seed}_p{seat}", "ok": False,
                "error": traceback.format_exc()[-2000:]}


def main():
    os.makedirs(TRAJ, exist_ok=True)
    tasks = []
    for name, path in AGENTS.items():
        for seed in SEEDS:
            for seat in (0, 1):
                if name == "v49":
                    # v49 reference: v49 vs v44 (avoid mirror self-play tape collision)
                    tasks.append((name, path, seed, seat))
                else:
                    tasks.append((name, path, seed, seat))
    # v49 games run vs v44 instead of mirror: patch after (opp handled in task)
    real_tasks = []
    for (name, path, seed, seat) in tasks:
        real_tasks.append((name, path, seed, seat))
    print(f"games: {len(real_tasks)}")
    # NOTE: v49-vs-v49 mirror would double-count; run v49 vs v44 and relabel:
    # implemented by swapping opp inside task via special-case below.
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {}
        for t in real_tasks:
            name, path, seed, seat = t
            if name == "v49":
                futs[ex.submit(task_v49, t)] = t
            else:
                futs[ex.submit(task, t)] = t
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            st = "OK" if r.get("ok") else "FAIL"
            print(f"[{done}/{len(real_tasks)}] {st} {r['task']} "
                  f"{r.get('mine', '')}/{r.get('opp', '')}", flush=True)
    with open(os.path.join(TRAJ, "_capture_index.json"), "w") as f:
        json.dump(results, f, indent=1)
    ok = sum(1 for r in results if r.get("ok"))
    print(f"captured {ok}/{len(results)}")


def task_v49(args):
    name, path, seed, seat = args
    try:
        v44 = os.path.join(REPO, AGENTS["v44"])
        rec = run_game(name, os.path.join(REPO, path), v44, seed, seat)
        rec["opp"] = "v44"
        fn = f"{name}_vs_v44_seed{seed}_p{seat}.json"
        with open(os.path.join(TRAJ, fn), "w") as f:
            json.dump(rec, f)
        r = rec["rewards"]
        return {"task": fn, "ok": True, "mine": r[seat], "opp": r[1 - seat],
                "win": r[seat] > r[1 - seat], "statuses": rec["statuses"]}
    except Exception:  # noqa: BLE001
        return {"task": f"{name}_vs_v44_seed{seed}_p{seat}", "ok": False,
                "error": traceback.format_exc()[-2000:]}


if __name__ == "__main__":
    main()
