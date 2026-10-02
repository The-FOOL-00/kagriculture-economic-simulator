#!/usr/bin/env python3
"""V58 V49-vs-elite comparison (committed).

1. Loads captured in-sim trajectories (research/v58/analysis/trajectories/).
2. Matches each executable agent's stream hashes against S3 elite h100/h200
   families (exact match => same route line through that turn).
3. Builds the strategy-lever difference matrix (V49 vs elite families F1..Fn
   and vs each executable elite): crops, crew, hires, land day, animals,
   market census, first sales, bank.
4. Writes V49_VS_ELITE.json, STRATEGY_SIGNATURE_SCHEMA.json, MISSING_LEVERS.md,
   MACRO_BOUNDARIES.md.
"""
import json
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
AN = os.path.join(REPO, "research", "v58", "analysis")
TRAJ = os.path.join(AN, "trajectories")
DB = os.path.join(REPO, "research", "v58", "data", "replay_database.jsonl")
CL = os.path.join(AN, "ELITE_STRATEGY_CLUSTERS.json")

sys.stdout.reconfigure(line_buffering=True)

CUTS = ["stream_h24", "stream_h48", "stream_h100", "stream_h136",
        "stream_h200", "stream_h300", "stream_h400", "stream_h719"]


def load_db_hashes():
    """elite hash -> family stats; all-seat hash counts for control overlap."""
    elite_h100 = defaultdict(list)
    elite_h200 = defaultdict(list)
    all_h100 = Counter()
    all_h200 = Counter()
    with open(DB) as f:
        for line in f:
            r = json.loads(line)
            h = r.get("hashes") or {}
            h100, h200 = h.get("stream_h100"), h.get("stream_h200")
            all_h100[h100] += 1
            all_h200[h200] += 1
            if (r.get("rating") or 0) >= 2945:
                elite_h100[h100].append(r)
                elite_h200[h200].append(r)
    return elite_h100, elite_h200, all_h100, all_h200


def traj_summary(fn):
    d = json.load(open(os.path.join(TRAJ, fn)))
    seat = d["seat"]
    s = d["seats"][seat]
    g = s["geo_features"]
    # animal/crop peaks from daily
    anim_peak, plant_peak, money_d, crew_d = {}, {}, [], []
    for snap in s["daily"]:
        money_d.append(snap["money"])
        crew_d.append(snap["crew"])
        for k, v in (snap.get("animals") or {}).items():
            anim_peak[k] = max(anim_peak.get(k, 0), v)
        for k, v in (snap.get("plants") or {}).items():
            plant_peak[k] = max(plant_peak.get(k, 0), v)
    r = d["rewards"]
    return {"file": fn, "agent": d["agent"], "seed": d["seed"], "seat": seat,
            "mine": r[seat], "opp": r[1 - seat], "win": r[seat] > r[1 - seat],
            "geo": g, "hashes": s["hashes"],
            "anim_peak": anim_peak, "plant_peak": plant_peak,
            "money_end": money_d[-1] if money_d else 0,
            "crew_max": max(crew_d) if crew_d else 0,
            "mkt": s["mkt_census"], "first_sale": s["first_sale"],
            "sale_qty": s["sale_qty"],
            "quads_end": (s["daily"][-1].get("quads") or []) if s["daily"] else []}


def main():
    clusters = json.load(open(CL))
    elite_h100, elite_h200, all_h100, all_h200 = load_db_hashes()
    print(f"elite h100 fams={len(elite_h100)} h200 fams={len(elite_h200)}")

    files = sorted(f for f in os.listdir(TRAJ) if f.endswith(".json") and not f.startswith("_"))
    by_agent = defaultdict(list)
    for fn in files:
        by_agent[traj_summary(fn)["agent"]].append(traj_summary(fn))
    print(f"agents captured: {sorted(by_agent)}")

    # hash-match each agent vs elite families
    agents = {}
    for agent, trajs in sorted(by_agent.items()):
        t0 = trajs[0]
        h100 = (t0["hashes"] or {}).get("stream_h100")
        h200 = (t0["hashes"] or {}).get("stream_h200")
        e100 = elite_h100.get(h100, [])
        e200 = elite_h200.get(h200, [])
        # earliest divergence cut vs the dominant elite family F1
        f1_h100 = clusters["families_stream_h100"]["top"][0]["hash"]
        agents[agent] = {
            "games": len(trajs),
            "wins_vs_v49_opp": sum(1 for t in trajs if t["win"]) if agent != "v49" else None,
            "mean_bank": sum(t["money_end"] for t in trajs) / len(trajs),
            "h100": h100, "h200": h200,
            "h100_in_elite": len(e100) > 0,
            "h100_elite_members": len(e100),
            "h100_elite_max_rating": max((m["rating"] for m in e100), default=None),
            "h100_all_seats_sharing": all_h100.get(h100, 0),
            "h200_in_elite": len(e200) > 0,
            "h200_elite_members": len(e200),
            "h200_all_seats_sharing": all_h200.get(h200, 0),
            "matches_F1_h100": h100 == f1_h100,
            "geo_med": {c: sorted((t["geo"][c] for t in trajs),
                                key=lambda v: (v is None, v))[len(trajs) // 2]
                        for c in ["peak_crew", "total_hires", "tiles_planted", "plants_carrot",
                                  "plants_melon", "plants_strawberry", "plants_tomato",
                                  "plants_wheat", "first_land_day", "final_money"]},
            "anim_peak": {k: max(t["anim_peak"].get(k, 0) for t in trajs)
                          for k in set().union(*(t["anim_peak"] for t in trajs))},
            "plant_peak": {k: max(t["plant_peak"].get(k, 0) for t in trajs)
                           for k in set().union(*(t["plant_peak"] for t in trajs))},
            "mkt": dict(Counter(k for t in trajs for k in t["mkt"])),
            "first_sale": trajs[0]["first_sale"],
            "quads_end": trajs[0]["quads_end"],
        }
        a = agents[agent]
        print(f"{agent}: bank={a['mean_bank']:.0f} h100_match_elite={a['h100_in_elite']} "
              f"(n={a['h100_elite_members']}, max_r={a['h100_elite_max_rating']}) "
              f"F1={a['matches_F1_h100']} wins={a['wins_vs_v49_opp']}")

    # difference matrix: V49 vs top elite families + executable elites
    fams = clusters["families_stream_h100"]["top"][:6]
    levers = ["peak_crew", "total_hires", "tiles_planted", "plants_melon",
              "plants_strawberry", "plants_wheat", "plants_carrot", "plants_tomato",
              "first_land_day", "final_money"]
    matrix = {"levers": levers,
              "V49": agents["v49"]["geo_med"],
              "families": {f"F{i+1}": {"n": f["size"], "rating_med": f["rating_med"],
                                       **{L: f["feature_med"].get(L) for L in levers}}
                           for i, f in enumerate(fams)},
              "executables": {k: v["geo_med"] for k, v in agents.items()}}
    with open(os.path.join(AN, "V49_VS_ELITE.json"), "w") as f:
        json.dump({"agents": agents, "matrix": matrix}, f, indent=1)

    # schema (canonical strategy signature incl. V58 extensions)
    schema = {
        "$schema": "v58/strategy_signature/1",
        "georgymamarin_base": ["peak_crew", "total_hires", "first_land_day", "elbow_day",
                               "tiles_planted", "plants_carrot", "plants_melon",
                               "plants_strawberry", "plants_tomato", "plants_wheat",
                               "price_*_min/max", "final_money"],
        "stream_hashes": CUTS,
        "v58_extended": ["daily.money", "daily.crew", "daily.animals{SPP:count}",
                         "daily.plants{CROP:count}", "daily.quads",
                         "market_census{OP:count}", "first_sale_day{PROD:day}",
                         "sale_qty{PROD:units}", "anim_peak{SPP:max}", "plant_peak{CROP:max}"],
        "provenance": "S2 definitions mirrored in capture_trajectories.py; hashes share S3 normalization",
    }
    with open(os.path.join(AN, "STRATEGY_SIGNATURE_SCHEMA.json"), "w") as f:
        json.dump(schema, f, indent=1)

    # macro boundaries: at which cut do top families diverge from each other / F1?
    tops = [(f["hash"], f["size"]) for f in clusters["families_stream_h100"]["top"][:12]]
    h200_of = {}
    with open(DB) as f:
        for line in f:
            r = json.loads(line)
            h = r.get("hashes") or {}
            if h.get("stream_h100") in dict(tops) and (r.get("rating") or 0) >= 2945:
                h200_of.setdefault(h.get("stream_h100"), Counter())[h.get("stream_h200")] += 1
    lines = ["# V58 Macro Boundaries", "",
             "Family = exact action-stream identity through turn N (S3 hashes).",
             "F1 (dominant elite route) splits after turn 100:", ""]
    for h100, n in tops:
        sub = h200_of.get(h100, {})
        lines.append(f"- h100 {h100}: n={n} -> {len(sub)} distinct h200 sub-routes "
                     f"(top3: {[f'{k[:8]}x{v}' for k, v in sub.most_common(3)]})")
    lines += ["",
              "Executable-agent hash placement vs elite families:",
              ""]
    for agent, a in sorted(agents.items()):
        lines.append(f"- {agent}: h100_in_elite={a['h100_in_elite']} "
                     f"(elite_n={a['h100_elite_members']}, all_n={a['h100_all_seats_sharing']}) "
                     f"h200_in_elite={a['h200_in_elite']} (elite_n={a['h200_elite_members']})")
    lines += ["",
              "## Decision-boundary reading",
              "Turn-100 identity already separates the two macro crop routes "
              "(24/42/108@land7 vs 19/37/143@land6); turn-200 identity splits execution "
              "variants within a macro route. A safe macro selector would therefore have "
              "to commit no later than ~turn 100 (day 4) to change macro route — but the "
              "captured executables show routes are committed at step 0 (tapes)."]
    with open(os.path.join(AN, "MACRO_BOUNDARIES.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote V49_VS_ELITE.json, STRATEGY_SIGNATURE_SCHEMA.json, MACRO_BOUNDARIES.md")


if __name__ == "__main__":
    main()
