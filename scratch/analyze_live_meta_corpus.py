import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
replay_dir = os.path.join(BASE_DIR, "replays", "live_tournament")

files = [f for f in os.listdir(replay_dir) if f.endswith(".json")]
print(f"Auditing {len(files)} official live tournament episodes...")

episodes_data = []

for fn in sorted(files):
    fp = os.path.join(replay_dir, fn)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        continue
        
    info = d.get("info", {})
    seed = info.get("seed") or d.get("configuration", {}).get("seed")
    teams = info.get("TeamNames", ["P0", "P1"])
    rewards = d.get("rewards") or [d["steps"][-1][0]["reward"], d["steps"][-1][1]["reward"]]
    steps = d.get("steps", [])
    
    if not steps or len(steps) < 100:
        continue

    # Determine which seat was our submission (Eldritch)
    our_seat = None
    opp_seat = None
    for p_idx in [0, 1]:
        t_name = teams[p_idx] if len(teams) > p_idx else ""
        if "Eldritch" in t_name or "561469" in t_name:
            our_seat = p_idx
            opp_seat = 1 - p_idx
            break
            
    if our_seat is None:
        our_seat = 0
        opp_seat = 1

    our_name = teams[our_seat] if len(teams) > our_seat else f"P{our_seat}"
    opp_name = teams[opp_seat] if len(teams) > opp_seat else f"P{opp_seat}"
    our_cash = rewards[our_seat]
    opp_cash = rewards[opp_seat]

    # Telemetry extraction for both players
    telemetry = {0: {}, 1: {}}
    for p_idx in [0, 1]:
        max_workers = 0
        max_cows = 0
        max_sheep = 0
        max_pastures = 0
        max_shed = 0
        crops_planted = {}
        items_sold = {}
        
        last_step_obs = steps[-1][p_idx].get("observation", {})
        shops = last_step_obs.get("town", {}).get("unlocked_shops", [])
        
        for s_idx, step_data in enumerate(steps):
            p_data = step_data[p_idx]
            obs = p_data.get("observation", {})
            farm = obs.get("farms", [{}, {}])[p_idx] if len(obs.get("farms", [])) > p_idx else {}
            private = obs.get("private", {})
            
            w_cnt = len(farm.get("hands", [])) + (1 if farm.get("farmer") else 0)
            max_workers = max(max_workers, w_cnt)
            
            cows = 0
            sheep = 0
            for row in farm.get("tiles", []):
                for t in row:
                    if isinstance(t, dict) and t.get("animal"):
                        if t["animal"] == "COW": cows += 1
                        elif t["animal"] == "SHEEP": sheep += 1
            max_cows = max(max_cows, cows)
            max_sheep = max(max_sheep, sheep)
            
            shed_total = sum(private.get("shed", {}).values()) if isinstance(private.get("shed"), dict) else 0
            max_shed = max(max_shed, shed_total)
            
            act = p_data.get("action", {})
            if isinstance(act, dict):
                for h in [act.get("farmer")] + act.get("hands", []):
                    if h and len(h) > 1 and h[0] == "PLANT":
                        crops_planted[h[1]] = crops_planted.get(h[1], 0) + 1
                for m in act.get("market", []):
                    if isinstance(m, list) and len(m) >= 3 and m[0] == "SELL":
                        items_sold[m[1]] = items_sold.get(m[1], 0) + int(m[2])
                        
        telemetry[p_idx] = {
            "max_workers": max_workers,
            "max_cows": max_cows,
            "max_sheep": max_sheep,
            "max_shed": max_shed,
            "crops_planted": crops_planted,
            "items_sold": items_sold,
            "unlocked_shops": shops
        }

    episodes_data.append({
        "file": fn,
        "seed": seed,
        "our_name": our_name,
        "opp_name": opp_name,
        "our_cash": our_cash,
        "opp_cash": opp_cash,
        "margin": our_cash - opp_cash,
        "won": our_cash > opp_cash,
        "shops": telemetry[our_seat]["unlocked_shops"][:4],
        "our_telemetry": telemetry[our_seat],
        "opp_telemetry": telemetry[opp_seat]
    })

# Summary Analysis
total_eps = len(episodes_data)
wins = sum(1 for e in episodes_data if e["won"])
losses = total_eps - wins
mean_margin = sum(e["margin"] for e in episodes_data) / total_eps

print("\n" + "=" * 100)
print(f"OFFICIAL LIVE TOURNAMENT CORPUS AUDIT (N={total_eps} Episodes)")
print("=" * 100)
print(f"Overall Record: {wins} Wins / {losses} Losses (Win Rate: {wins/total_eps*100:.1f}%)")
print(f"Mean Margin:    ${mean_margin:+,.2f}")

# Top Opponents
opp_stats = {}
for e in episodes_data:
    opp = e["opp_name"].split()[0] # clean name
    if opp not in opp_stats:
        opp_stats[opp] = {"count": 0, "wins": 0, "margins": [], "opp_cashes": []}
    opp_stats[opp]["count"] += 1
    if not e["won"]:
        opp_stats[opp]["wins"] += 1 # opponent won
    opp_stats[opp]["margins"].append(e["margin"])
    opp_stats[opp]["opp_cashes"].append(e["opp_cash"])

print("\nTOP OPPONENTS RANKED BY FREQUENCY & THREAT:")
print(f"{'Opponent':<20} | {'Matches':<8} | {'Opp Wins':<9} | {'Mean Margin':<14} | {'Opp Mean Cash':<14}")
print("-" * 75)
for opp, st in sorted(opp_stats.items(), key=lambda x: -x[1]["count"]):
    m_margin = sum(st["margins"]) / st["count"]
    m_cash = sum(st["opp_cashes"]) / st["count"]
    print(f"{opp:<20} | {st['count']:<8} | {st['wins']:<9} | ${m_margin:>+12,.0f} | ${m_cash:>12,.0f}")

with open("scratch/live_meta_corpus_summary.json", "w") as f:
    json.dump(episodes_data, f, indent=2)

print("\nLive meta summary saved to scratch/live_meta_corpus_summary.json")
