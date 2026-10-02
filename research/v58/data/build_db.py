#!/usr/bin/env python3
"""V58 replay database builder (committed, reproducible).

Sources (all local, no Kaggle access, no holdouts):
  S1  replays/raw/georgymamarin/episodes.csv          74,699 episodes, per-seat rating/bank
  S2  replays/raw/georgymamarin/episode_features.csv  139,903 (episode,seat) behavior features
  S3  replays/raw/georgymamarin/stream_hashes.csv     action-stream lineage hashes (8 cuts)
  S4  replays/raw/georgymamarin/teams.csv             7,090 teams, ladder snapshot
  S5  live_data/episodes_v31r2/keep/*.json            184 kept live replays (weak opp)
  S6  replays/live_tournament/*.json                  48 live tournament replays (weak opp)
  S7  external_repos/.../online_replays/{A,B,C1,C2}   48 cohort replays (sub-2800)
  S8  replays/episode-*-replay.json                   27 root replays (weak opp)
  S9  live leaderboard CSV 2026-09-22                 9,807 teams (score join key)
  S10 executable elite agents (elite corpus + P3090/P3000/night_harvest + replay_* tapes)

Outputs:
  research/v58/data/replay_manifest.json
  research/v58/data/replay_database.jsonl   (one row per seat, S1+S2+S3 joined)
  research/v58/data/replay_file_index.jsonl (one row per local replay file, S5-S9 joined)
"""
import csv
import glob
import hashlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(REPO, "research", "v58", "data")
GEO = os.path.join(REPO, "replays", "raw", "georgymamarin")

sys.stdout.reconfigure(line_buffering=True)


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def r1(x):
    try:
        return round(float(x), 1)
    except (TypeError, ValueError):
        return None


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {"sources": {}, "notes": []}

    # ---- S4 teams ----
    teams = {}
    tp = os.path.join(GEO, "teams.csv")
    with open(tp, newline="") as f:
        for row in csv.DictReader(f):
            teams[row["team_id"]] = {"name": row["team_name"], "ladder": r1(row["ladder_score"])}
    manifest["sources"]["S4_teams_csv"] = {"path": os.path.relpath(tp, REPO), "teams": len(teams),
                                           "sha16": sha16(tp)}

    # ---- S1 episodes ----
    eps = {}
    ep = os.path.join(GEO, "episodes.csv")
    with open(ep, newline="") as f:
        for row in csv.DictReader(f):
            eps[row["episode_id"]] = row
    manifest["sources"]["S1_episodes_csv"] = {"path": os.path.relpath(ep, REPO),
                                              "episodes": len(eps), "sha16": sha16(ep)}

    # ---- S2 features ----
    feats = {}
    fp = os.path.join(GEO, "episode_features.csv")
    with open(fp, newline="") as f:
        for row in csv.DictReader(f):
            feats[(row["episode_id"], row["seat"])] = row
    manifest["sources"]["S2_features_csv"] = {"path": os.path.relpath(fp, REPO),
                                              "rows": len(feats), "sha16": sha16(fp)}

    # ---- S3 stream hashes ----
    hashes = {}
    hp = os.path.join(GEO, "stream_hashes.csv")
    with open(hp, newline="") as f:
        for row in csv.DictReader(f):
            hashes[(row["episode_id"], row["seat"])] = row
    manifest["sources"]["S3_hashes_csv"] = {"path": os.path.relpath(hp, REPO),
                                            "rows": len(hashes), "sha16": sha16(hp)}

    # ---- S9 leaderboard CSV (score join for local replays) ----
    lb = {}
    lbp = os.path.join(REPO, "live_data", "episodes_v31r2",
                       "kaggriculture-publicleaderboard-2026-09-22T08:50:44.csv")
    with open(lbp, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            lb[row["TeamName"]] = r1(row["Score"])
    manifest["sources"]["S9_leaderboard_csv"] = {"path": os.path.relpath(lbp, REPO),
                                                 "teams": len(lb), "sha16": sha16(lbp)}

    # ---- replay_database.jsonl: S1+S2+S3 joined per seat ----
    dbp = os.path.join(OUT, "replay_database.jsonl")
    n_db, n_elite = 0, 0
    feat_cols = ["engine_version", "final_money", "peak_crew", "total_hires",
                 "first_land_day", "elbow_day", "tiles_planted", "plants_carrot",
                 "plants_melon", "plants_strawberry", "plants_tomato", "plants_wheat"]
    hash_cols = ["turns", "stream_h24", "stream_h48", "stream_h100", "stream_h136",
                 "stream_h200", "stream_h300", "stream_h400", "stream_h719"]
    with open(dbp, "w") as out:
        for eid, e in eps.items():
            for seat in ("0", "1"):
                other = "1" if seat == "0" else "0"
                rating = r1(e[f"rating_{seat}"])
                bank = r1(e[f"bank_{seat}"])
                obank = r1(e[f"bank_{other}"])
                outcome = "W" if (bank or -1) > (obank or -1) else ("L" if (bank or -1) < (obank or -1) else "D")
                fr = feats.get((eid, seat), {})
                hh = hashes.get((eid, seat), {})
                team_id = e[f"team_{seat}"]
                rec = {"episode_id": int(eid), "date": e["create_time"][:10],
                       "type": e["type"], "seat": int(seat),
                       "team_id": team_id, "team_name": teams.get(team_id, {}).get("name"),
                       "rating": rating, "bank": bank, "opp_bank": obank,
                       "outcome": outcome,
                       "features": {c: (fr.get(c) if c == "engine_version" else r1(fr.get(c))) for c in feat_cols},
                       "hashes": {c: hh.get(c) for c in hash_cols}}
                out.write(json.dumps(rec) + "\n")
                n_db += 1
                if rating is not None and rating >= 2945:
                    n_elite += 1
    manifest["outputs"] = {"replay_database.jsonl": {"rows": n_db, "elite_ge2945": n_elite}}

    # ---- replay_file_index.jsonl: local replay files ----
    patterns = {"S5_keep": "live_data/episodes_v31r2/keep/*.json",
                "S6_live_tournament": "replays/live_tournament/*.json",
                "S7_cohorts": "external_repos/lixingtao123-Kaggriculture/online_replays/*/*.json",
                "S8_root": "replays/episode-*-replay.json"}
    idxp = os.path.join(OUT, "replay_file_index.jsonl")
    n_idx = 0
    with open(idxp, "w") as out:
        for sid, pat in patterns.items():
            files = sorted(glob.glob(os.path.join(REPO, pat)))
            manifest["sources"][sid] = {"pattern": pat, "files": len(files)}
            for fp2 in files:
                try:
                    d = json.load(open(fp2))
                    info = d.get("info", {}) or {}
                    teams2 = info.get("TeamNames", []) or []
                    rec = {"file": os.path.relpath(fp2, REPO), "source": sid,
                           "episode_id": info.get("EpisodeId"), "seed": info.get("seed"),
                           "teams": [{"name": t, "score": lb.get(t)} for t in teams2],
                           "rewards": d.get("rewards"), "statuses": d.get("statuses"),
                           "steps": len(d.get("steps", []))}
                except Exception as ex:  # noqa: BLE001
                    rec = {"file": os.path.relpath(fp2, REPO), "source": sid, "error": str(ex)[:200]}
                out.write(json.dumps(rec) + "\n")
                n_idx += 1
    manifest["outputs"]["replay_file_index.jsonl"] = {"rows": n_idx}

    manifest["notes"] = [
        "No 3100+ full-replay archive exists locally; S1-S3 carry 3100+ SEATS as (rating, features, hashes) only.",
        "S5-S8 local replays are near-exclusively sub-2800 opponents; unsuitable as elite population.",
        "Elite population for V58 = S1+S2+S3 seats with rating>=2945 (518 seats, 2026-08-05..15, engines 1.32.4-6).",
        "Engine caveat: only 1 elite seat played on 1.32.7; strategy-family discovery is cross-patch, causal tests run on 1.32.7.",
    ]
    with open(os.path.join(OUT, "replay_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
