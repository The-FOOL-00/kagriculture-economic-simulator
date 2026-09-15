import os
import json

res_dir = r"external_repos\lixingtao123-Kaggriculture\results"
summary = []

for f in os.listdir(res_dir):
    if not f.endswith(".json"):
        continue
    fp = os.path.join(res_dir, f)
    try:
        with open(fp, "r", encoding="utf-8") as jf:
            d = json.load(jf)
            if isinstance(d, dict):
                # check summary or aggregate or direct keys
                if "summary" in d:
                    s = d["summary"]
                    summary.append({
                        "file": f,
                        "candidate": s.get("candidate", ""),
                        "opponent": s.get("opponent", ""),
                        "games": s.get("games"),
                        "win_rate": s.get("win_rate"),
                        "wins": s.get("wins"),
                        "mean_margin": s.get("mean_margin"),
                        "mean_reward": s.get("mean_reward")
                    })
                elif "aggregate" in d:
                    a = d["aggregate"]
                    summary.append({
                        "file": f,
                        "candidate": "aggregate",
                        "opponent": "replay",
                        "games": a.get("games"),
                        "win_rate": (a.get("wins", 0) / a.get("games", 1)) if a.get("games") else None,
                        "wins": a.get("wins"),
                        "mean_margin": a.get("mean_margin"),
                        "mean_reward": a.get("mean_reward")
                    })
    except Exception as e:
        pass

print(f"Parsed {len(summary)} result summaries from results/")

# Search for 100% win rate and 10% win rate
print("\n--- 100% Win Rate Files ---")
for s in summary:
    if s.get("win_rate") == 1.0 or s.get("win_rate") == 100:
        print(f"  {s['file']}: cand={s['candidate']} vs opp={s['opponent']}, games={s['games']}, margin={s['mean_margin']}")

print("\n--- ~10% Win Rate Files ---")
for s in summary:
    wr = s.get("win_rate")
    if wr is not None and 0.05 <= wr <= 0.15:
        print(f"  {s['file']}: cand={s['candidate']} vs opp={s['opponent']}, games={s['games']}, win_rate={wr}, margin={s['mean_margin']}")

print("\n--- Files mentioning h3q4 / h4 ---")
for s in summary:
    if "h3" in s["file"] or "h4" in s["file"] or "h3" in str(s["candidate"]) or "h4" in str(s["candidate"]):
        print(f"  {s['file']}: cand={s['candidate']} vs opp={s['opponent']}, games={s['games']}, win_rate={s['win_rate']}, margin={s['mean_margin']}")

with open(r"forensic_verification\benchmark_raw\lixingtao_results_audit.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
