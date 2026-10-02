#!/usr/bin/env python3
"""V60 — Targeted Sep 22 elite discovery.

Strategy:
1. The georgymamarin corpus ends Aug 31, so ALL Aug submissions are known.
2. Sep submissions have higher IDs than Aug ones.
3. From the last known Aug submission ID, scan upward to find Sep ones.
4. Then specifically target DSM, Vadim Vasilenko, etc. by querying ListEpisodes
   for a range of high submission IDs we don't have yet.
5. Alternative: use the agents.csv teamId for known teams to find their NEW sub IDs.

Also: check episode_features.csv for team_name data that might have Sep info.
"""
import csv, gzip, json, sys, time, requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

GEORGYMAMARIN = Path("replays/raw/georgymamarin")
OUT_DIR = Path("research/v60/data")
REPLAY_OUT = OUT_DIR / "sep_replays"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

session = requests.Session()
session.headers["User-Agent"] = "kaggriculture-v60-research"

# ===== STEP 1: Find the highest Aug submission IDs =====
print("=== STEP 1: Find Aug submission ID ceiling ===")
with open(GEORGYMAMARIN / "state.json") as f:
    state = json.load(f)

all_subs = sorted(set(state['submissions']), reverse=True)
print(f"Total unique sub IDs: {len(all_subs)}")
print(f"Highest 10: {all_subs[:10]}")
print(f"Lowest 10:  {all_subs[-10:]}")

max_aug_sub = all_subs[0]  # Highest known Aug sub ID
print(f"\nHighest Aug sub ID: {max_aug_sub}")

# ===== STEP 2: Check episode_features.csv for team names =====
print("\n=== STEP 2: Check episode_features.csv ===")
features_file = GEORGYMAMARIN / "episode_features.csv"
if features_file.exists():
    with open(features_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"Columns: {cols}")
        rows = list(reader)
    print(f"Total rows: {len(rows)}")
    print(f"Sample: {rows[0]}" if rows else "empty")

# ===== STEP 3: Use team IDs from teams.csv to find new submissions =====
print("\n=== STEP 3: Search agents.csv for known team IDs, find latest subs =====")

# Team IDs we found earlier
TARGET_TEAM_IDS = {
    '16730524': 'THIRD FARM CLUB',
    '16681125': 'M & M & P & Q',
    '16718819': 'Majkel1337',
}

# Also look for unknown teams in teams.csv (DSM, Vadim Vasilenko, etc.)
TARGET_NAMES = {"DSM", "Vadim Vasilenko", "Unknown Mother-Goose", "Kaggledew Valley",
                "ymg_aq", "KawattaTaido", "Otter Vibe", "mtmr_s1", "QQ", "DECEM",
                "Planned Economy", "DeeperNet", "Orbital Terraformer", "midnq",
                "SpaTaro", "Ryo Hasegawa", "RS Turley", "Densike", "TheEggman",
                "kwa", "Yannik Schiffner", "Azat Akhtyamov", "Sida Zuo",
                "THUNDER THUNDER"}

with open(GEORGYMAMARIN / "teams.csv", encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('team_name') in TARGET_NAMES:
            TARGET_TEAM_IDS[row['team_id']] = row['team_name']
            print(f"  Found: {row['team_name']} -> id {row['team_id']}, score {row.get('ladder_score')}")

print(f"\nTarget team IDs: {TARGET_TEAM_IDS}")

# Find all submissions for target teams from agents.csv
team_to_subs = {tid: [] for tid in TARGET_TEAM_IDS}
with open(GEORGYMAMARIN / "agents.csv", encoding='utf-8') as f:
    for row in csv.DictReader(f):
        tid = str(row.get('team_id', ''))
        if tid in TARGET_TEAM_IDS:
            sub_id = row.get('submission_id')
            if sub_id:
                team_to_subs[tid].append(int(sub_id))

print("\nKnown submissions per target team:")
all_target_subs = set()
for tid, subs in team_to_subs.items():
    latest = sorted(subs)[-5:] if subs else []
    all_target_subs.update(subs)
    print(f"  {TARGET_TEAM_IDS[tid]}: {len(subs)} total, latest: {latest}")

# ===== STEP 4: Scan submission IDs just above max_aug_sub for Sep activity =====
print(f"\n=== STEP 4: Scan submission IDs above {max_aug_sub} for Sep activity ===")
# Sep submissions will be created after the last Aug submission
# Try IDs from max_aug_sub upward in steps 

sep_sub_ids = []
sep_episodes_all = {}

# Probe in bands above the highest known Aug sub ID
scan_start = max_aug_sub + 1
scan_range = 50000  # Try 50k IDs above
step_size = 500     # Sample every 500th

probe_ids = list(range(scan_start, scan_start + scan_range, step_size))
print(f"Probing {len(probe_ids)} IDs from {scan_start} to {scan_start + scan_range}")

found_sep = 0
for i, sub_id in enumerate(probe_ids):
    if i % 10 == 0:
        print(f"  Probing {sub_id} ({i}/{len(probe_ids)}), Sep found: {found_sep}")
    
    try:
        r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=15)
        if r.status_code == 200:
            eps = r.json().get("episodes", [])
            if eps:  # This sub ID exists and has episodes
                sep_eps = [e for e in eps if (e.get('endTime') or '').startswith('2026-09')]
                latest = max((e.get('endTime','') or '') for e in eps)
                if sep_eps:
                    print(f"  *** FOUND Sep sub: {sub_id} -> {len(sep_eps)} Sep eps, latest {latest[:10]}")
                    sep_sub_ids.append(sub_id)
                    found_sep += 1
                    for e in sep_eps:
                        eid = str(e.get('id', ''))
                        if eid:
                            sep_episodes_all[eid] = e
                    # Also get opponent sub IDs from these Sep episodes
                    for e in sep_eps:
                        for a in e.get('agents', []):
                            new_sid = a.get('submissionId')
                            if new_sid and new_sid not in probe_ids:
                                probe_ids.append(new_sid)
                else:
                    pass  # Has episodes but none in Sep
            time.sleep(0.3)
        elif r.status_code == 429:
            print(f"  Rate limited, sleeping...")
            time.sleep(15)
        # 404 = sub ID doesn't exist, skip silently
    except Exception as e:
        print(f"  Sub {sub_id}: {e}")
        time.sleep(1)

print(f"\n=== Sep episodes found: {len(sep_episodes_all)} ===")
print(f"Sep submission IDs: {sep_sub_ids}")

# ===== STEP 5: Download found Sep replays =====
if sep_episodes_all:
    print(f"\n=== STEP 5: Download {min(100, len(sep_episodes_all))} Sep replays ===")
    for ep_id in list(sep_episodes_all.keys())[:100]:
        out_path = REPLAY_OUT / f"sep_{ep_id}.json.gz"
        if out_path.exists():
            continue
        try:
            r = session.get(REPLAY_URL.format(id=ep_id), timeout=60)
            if r.status_code == 200:
                out_path.write_bytes(gzip.compress(r.content, 6))
                ep = sep_episodes_all[ep_id]
                agents = ep.get('agents', [])
                end = (ep.get('endTime','') or '')[:16]
                print(f"  [OK] ep {ep_id}: {len(r.content)//1024}KB | {end}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [ERR] {e}")

with open(OUT_DIR / 'sep_scan_result.json', 'w') as f:
    json.dump({
        'max_aug_sub': max_aug_sub,
        'scan_start': scan_start,
        'sep_sub_ids': sep_sub_ids,
        'sep_episodes_count': len(sep_episodes_all),
    }, f, indent=2)

print(f"\nFiles in sep_replays: {len(list(REPLAY_OUT.glob('*.json.gz')))}")
