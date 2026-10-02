#!/usr/bin/env python3
"""V60 — Download episode replays via direct Kaggle HTTP API.
Uses the competitions episodes + replay endpoints that work with basic auth.
Also tries to list current team-submissions for top players.
"""
import requests
import json
import os
import time
from pathlib import Path

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 30

BASE = "https://www.kaggle.com/api/v1"
OUT_DIR = Path("research/v60/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def api_get(url, params=None):
    r = requests.get(url, auth=auth, params=params, timeout=TIMEOUT)
    return r

# ===== APPROACH 1: Get our own submission episodes =====
print("=== APPROACH 1: Get current submission episodes ===")

# Get list of our active submissions
r = api_get(f"{BASE}/competitions/kaggriculture/submissions?format=json")
print(f"Submissions endpoint: {r.status_code}")
if r.status_code == 200:
    try:
        subs = r.json()
        print(f"Submissions: {len(subs)}")
        for s in subs[:5]:
            print(f"  {s}")
    except:
        print(f"  Body: {r.text[:300]}")
else:
    print(f"  Body: {r.text[:300]}")

# ===== APPROACH 2: Get team-submissions for top players =====
print("\n=== APPROACH 2: Get team-submissions for top Sep 22 teams ===")

# kaggle competitions team-submissions lists public submissions
# Slug for kaggriculture competition
COMP = "kaggriculture"

# Known Sep 22 top teams and their possible Kaggle usernames
target_teams = [
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
]

# Try team-submissions endpoint for the competition
r = api_get(f"{BASE}/competitions/{COMP}/team-submissions", 
            params={"format": "json", "maxSize": 20})
print(f"Team submissions: {r.status_code}")
if r.status_code == 200:
    try:
        ts = r.json()
        print(f"Team submissions: {len(ts)}")
        with open(OUT_DIR / 'team_submissions.json', 'w') as f:
            json.dump(ts, f, indent=2)
        for sub in ts[:10]:
            print(f"  {sub}")
    except:
        print(f"  Body: {r.text[:500]}")
else:
    print(f"  Body: {r.text[:300]}")

# ===== APPROACH 3: Use competitions leaderboard API to get submission IDs =====
print("\n=== APPROACH 3: Competition leaderboard with submission IDs ===")

r = api_get(f"{BASE}/competitions/{COMP}/leaderboard/view", 
            params={"format": "json"})
print(f"Leaderboard view: {r.status_code}")
if r.status_code == 200:
    try:
        lb = r.json()
        print(f"Leaderboard type: {type(lb)}")
        if isinstance(lb, dict):
            print(f"Keys: {list(lb.keys())}")
            entries = lb.get('submissions', lb.get('results', lb.get('data', [])))
        elif isinstance(lb, list):
            entries = lb
        else:
            entries = []
        print(f"Entries: {len(entries)}")
        with open(OUT_DIR / 'leaderboard_view.json', 'w') as f:
            json.dump(lb, f, indent=2)
        for e in entries[:10]:
            print(f"  {e}")
    except Exception as ex:
        print(f"  Parse error: {ex}")
        print(f"  Body: {r.text[:500]}")
else:
    print(f"  Body: {r.text[:300]}")

# ===== APPROACH 4: Try episodes endpoint directly via HTTP =====
print("\n=== APPROACH 4: Competition episodes via HTTP ===")

# Try various episode listing endpoints
for endpoint in [
    f"{BASE}/competitions/{COMP}/episodes",
    f"https://www.kaggle.com/api/v1/competitions/episodes?competitionSlug={COMP}&pageSize=5",
]:
    r = api_get(endpoint)
    print(f"  {endpoint}: {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"  Type: {type(data)}, {str(data)[:200]}")
        except:
            print(f"  Body: {r.text[:200]}")
    print()

# ===== APPROACH 5: Try downloading replay via HTTP directly =====
print("\n=== APPROACH 5: Download episode replay via HTTP ===")
# Episode 111851139 = a7 episode we already have locally

test_episode_id = 111851139
for replay_url in [
    f"{BASE}/competitions/{COMP}/episodes/{test_episode_id}/replay",
    f"https://www.kaggle.com/api/i/competitions.EpisodesService/GetEpisodeReplay",
    f"https://www.kaggle.com/api/v1/competitions/replay/{test_episode_id}",
]:
    try:
        r = requests.get(replay_url, auth=auth, timeout=TIMEOUT)
        print(f"  {replay_url}: {r.status_code}")
        ct = r.headers.get('content-type', '')
        if r.status_code == 200:
            print(f"    Content-Type: {ct}")
            print(f"    Size: {len(r.content)}")
            print(f"    Preview: {r.text[:200]}")
        elif r.status_code != 404:
            print(f"    Body: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")
    print()
