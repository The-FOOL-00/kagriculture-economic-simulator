#!/usr/bin/env python3
"""V60 — Acquire September 2026 elite replays using the same method as georgymamarin/scrape.py.

Method:
1. Use ListEpisodes API (no auth required) to get episode lists for Sep 22 top teams
2. Download replays from public CDN: https://www.kaggleusercontent.com/episodes/{id}.json

The state.json contains 26,571 submission IDs collected up to Aug 31.
The Sep 22 leaderboard top teams have NEW submission IDs we need to discover.

The episodes.csv contains episode metadata up to the crawl cutoff.
We can check if Sep episodes are already in episodes.csv, and find team names via teams.csv.
"""
import csv
import gzip
import json
import sys
import time
import os
import requests
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

GEORGYMAMARIN = Path("replays/raw/georgymamarin")
STATE_FILE = GEORGYMAMARIN / "state.json"
EPISODES_CSV = GEORGYMAMARIN / "episodes.csv"
TEAMS_CSV = GEORGYMAMARIN / "teams.csv"
AGENTS_CSV = GEORGYMAMARIN / "agents.csv"

OUT_DIR = Path("research/v60/data")
REPLAY_OUT = OUT_DIR / "sep_replays"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

# Sep 22 target teams
TARGET_TEAMS = {
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
}

session = requests.Session()
session.headers["User-Agent"] = "kaggriculture-v60-research"

# ===== STEP 1: Load teams.csv to find team IDs for target teams =====
print("=== STEP 1: Load teams.csv ===")
team_name_to_id = {}
team_id_to_name = {}
with open(TEAMS_CSV, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tid = row.get('team_id', row.get('id', ''))
        tname = row.get('team_name', row.get('name', ''))
        score = row.get('score', '')
        if tname in TARGET_TEAMS:
            team_name_to_id[tname] = tid
            team_id_to_name[tid] = tname
            print(f"  Found: {tname} -> id={tid}, score={score}")

print(f"\nTarget teams found in teams.csv: {len(team_name_to_id)}/{len(TARGET_TEAMS)}")
missing = TARGET_TEAMS - set(team_name_to_id.keys())
if missing:
    print(f"Missing from teams.csv: {missing}")

# ===== STEP 2: Search episodes.csv for episodes with target team IDs =====
print("\n=== STEP 2: Search episodes.csv for target team episodes ===")
target_ids = set(team_name_to_id.values())
sep_episodes = []
all_episodes_count = 0
with open(EPISODES_CSV, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_episodes_count += 1
        team_0 = str(row.get('team_0', ''))
        team_1 = str(row.get('team_1', ''))
        end_time = row.get('end_time', '')
        if team_0 in target_ids or team_1 in target_ids:
            ep = {
                'episode_id': row.get('episode_id', ''),
                'end_time': end_time,
                'team_0': team_0,
                'team_1': team_1,
                'bank_0': row.get('bank_0'),
                'bank_1': row.get('bank_1'),
                'rating_0': row.get('rating_0'),
                'rating_1': row.get('rating_1'),
                'sub_0': row.get('sub_0'),
                'sub_1': row.get('sub_1'),
                'team_0_name': team_id_to_name.get(team_0, '?'),
                'team_1_name': team_id_to_name.get(team_1, '?'),
            }
            sep_episodes.append(ep)

print(f"Total episodes in CSV: {all_episodes_count:,}")
print(f"Episodes involving target teams: {len(sep_episodes)}")

if sep_episodes:
    dates = sorted(ep['end_time'][:10] for ep in sep_episodes if ep['end_time'])
    print(f"Date range: {dates[0]} - {dates[-1]}")
    # Show Sep episodes
    sep_only = [ep for ep in sep_episodes if ep.get('end_time', '') >= '2026-09-01']
    print(f"September episodes: {len(sep_only)}")
    for ep in sep_only[:20]:
        print(f"  {ep['episode_id']} | {ep['end_time'][:10]} | {ep['team_0_name']} vs {ep['team_1_name']} | banks: {ep['bank_0']}/{ep['bank_1']}")

# ===== STEP 3: Find submission IDs for target teams in state.json =====
print("\n=== STEP 3: Get submission IDs from agents.csv ===")
target_sub_ids = set()
with open(AGENTS_CSV, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tid = str(row.get('team_id', ''))
        if tid in target_ids:
            sub_id = row.get('submission_id')
            if sub_id:
                target_sub_ids.add(int(sub_id))

print(f"Submission IDs for target teams: {len(target_sub_ids)}")
print(f"  {sorted(target_sub_ids)[-20:]}")  # Show most recent

# ===== STEP 4: Query ListEpisodes for target submission IDs =====
print("\n=== STEP 4: Query ListEpisodes API for target submissions ===")
new_episodes = {}
for sub_id in sorted(target_sub_ids, reverse=True)[:30]:  # Try 30 most recent
    try:
        r = session.post(LIST_URL, json={"submissionId": sub_id}, timeout=30)
        if r.status_code == 200:
            eps = r.json().get("episodes", [])
            print(f"  Sub {sub_id}: {len(eps)} episodes")
            for ep in eps:
                eid = str(ep.get('id', ''))
                if eid:
                    new_episodes[eid] = ep
            time.sleep(1.0)
        elif r.status_code == 429:
            print(f"  Sub {sub_id}: rate limited")
            time.sleep(5)
        else:
            print(f"  Sub {sub_id}: status {r.status_code}")
    except Exception as e:
        print(f"  Sub {sub_id}: error {e}")

print(f"\nNew episodes from ListEpisodes: {len(new_episodes)}")
# Filter to September
sep_new = {k: v for k, v in new_episodes.items() 
           if (v.get('endTime') or '') >= '2026-09-01'}
print(f"September episodes from new crawl: {len(sep_new)}")
for eid, ep in sorted(sep_new.items(), key=lambda x: x[1].get('endTime',''), reverse=True)[:20]:
    agents = ep.get('agents', [])
    teams = [a.get('teamId', '?') for a in agents]
    end = (ep.get('endTime', '') or '')[:16]
    print(f"  ep {eid} | {end} | teams {teams}")

# Save episode manifest
with open(OUT_DIR / 'sep_elite_episodes.json', 'w') as f:
    json.dump({'known_sep': sep_episodes, 'new_sep': list(sep_new.values())}, f, indent=2)

# ===== STEP 5: Download a sample of Sep elite replays =====
print("\n=== STEP 5: Download Sep elite replays from CDN ===")

# Get all Sep episode IDs to try
episode_ids_to_download = []
for ep in sep_only:  # from CSV
    episode_ids_to_download.append(ep['episode_id'])
for eid in list(sep_new.keys()):  # from new crawl
    if eid not in episode_ids_to_download:
        episode_ids_to_download.append(eid)

print(f"Total Sep elite episodes to download: {len(episode_ids_to_download)}")
print(f"  From CSV: {len(sep_only)}")
print(f"  From new crawl: {len(sep_new)}")

downloaded = 0
failed = 0
for ep_id in episode_ids_to_download[:50]:  # Cap at 50 for now
    out_path = REPLAY_OUT / f"sep_elite_{ep_id}.json.gz"
    if out_path.exists():
        downloaded += 1
        continue
    
    url = REPLAY_URL.format(id=ep_id)
    try:
        r = session.get(url, timeout=60)
        if r.status_code == 200:
            compressed = gzip.compress(r.content, 6)
            out_path.write_bytes(compressed)
            size_kb = len(r.content) // 1024
            print(f"  [OK] ep {ep_id}: {size_kb:,} KB")
            downloaded += 1
        elif r.status_code == 404:
            print(f"  [404] ep {ep_id}: not available")
            failed += 1
        else:
            print(f"  [{r.status_code}] ep {ep_id}")
            failed += 1
        time.sleep(0.5)
    except Exception as e:
        print(f"  [ERR] ep {ep_id}: {e}")
        failed += 1

print(f"\nDownload complete: {downloaded} downloaded, {failed} failed")
print(f"Output dir: {REPLAY_OUT}")
print(f"Files in output: {len(list(REPLAY_OUT.glob('*.json.gz')))}")
