# V60 Acquisition Commands — PowerShell
# Generated: 2026-09-28
# Purpose: Acquire September 2026 Kaggriculture episode replays for current 3000+ elite analysis.

# ============================================================
# ESTABLISHED WORKING METHODS
# ============================================================

# METHOD 1: kaggleusercontent CDN (NO AUTH REQUIRED)
# Download any episode replay by ID directly from public CDN
# REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode_id}.json"
# Example:
Invoke-WebRequest -Uri "https://www.kaggleusercontent.com/episodes/111851139.json" -OutFile "ep_111851139.json"

# METHOD 2: ListEpisodes API (requires POST, returns episode lists for a submissionId)
# POST to: https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes
# Body: {"submissionId": <integer>}
# Returns: {"episodes": [...]} with endTime, agents.submissionId fields
python -c "
import requests, json
r = requests.post('https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes',
    json={'submissionId': 55903635}, timeout=30)
print(r.json()['episodes'][:2])
"

# METHOD 3: Kaggle dataset list API (auth required, returns metadata only)
# Works for discovering datasets but NOT for downloading content
python -c "
import requests, json
creds = json.load(open('C:/Users/Sundareswaran/.kaggle/kaggle.json'))
r = requests.get('https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes',
    auth=(creds['username'], creds['key']), timeout=20)
print([d['ref'] for d in r.json()])
"

# ============================================================
# FAILED METHODS (DO NOT RETRY)
# ============================================================

# BLOCKED: kaggle CLI (ConnectionResetError on SSL handshake for auth)
# kaggle datasets download kaggle/kaggriculture-episodes-2026-09-26
# kaggle competitions replay 111851139

# BLOCKED: Dataset download API (/api/v1/datasets/{owner}/{name}/download)
# Returns 302 redirect to login page even with valid API key
# Requires browser session cookie, not API key authentication

# BLOCKED: Competition endpoints (/api/v1/competitions/{slug}/...)
# Returns 404 for all episode/leaderboard/submission endpoints

# ============================================================
# NEXT ACQUISITION STEPS FOR SEPTEMBER ELITE DATA
# ============================================================

# STEP 1: Find September submission IDs by scanning above highest Aug ID
# The georgymamarin state.json highest Aug sub ID is ~55904253
# Sep submissions will have IDs > this value
# Probe: 55904253 to 55954253 in steps of 100

python -X utf8 research/v60/data/scan_sep_subs.py

# STEP 2: Once Sep sub IDs found, download replays:
python -X utf8 -c "
import requests, gzip, json, time
from pathlib import Path
session = requests.Session()
sep_sub_id = REPLACE_WITH_FOUND_SUB_ID
r = session.post('https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes',
    json={'submissionId': sep_sub_id}, timeout=30)
for ep in r.json().get('episodes', []):
    if ep.get('endTime','').startswith('2026-09'):
        ep_id = ep['id']
        blob = session.get(f'https://www.kaggleusercontent.com/episodes/{ep_id}.json', timeout=60)
        Path(f'research/v60/data/sep_replays/sep_{ep_id}.json.gz').write_bytes(gzip.compress(blob.content, 6))
        time.sleep(0.4)
"

# ============================================================
# KNOWN DATASET SLUGS (Kaggle API searchable, not downloadable via API key)
# ============================================================
# georgymamarin/kaggriculture-episodes  (v77, updated 2026-09-28) — main corpus
# kaggle/kaggriculture-episodes-index   (v60, updated 2026-09-28) — daily index
# kaggle/kaggriculture-episodes-2026-09-26 (v1)                  — Sep 26 daily
# ashok205/kaggriculture-top10-replay-archive (v41, 3.96GB)      — TOP 10 archive
# xishengfeng/kaggriculture-replay-db (v5, 2.08GB)               — replay DB

# REQUIRED ACTION FOR USER:
# Log into Kaggle web UI and download:
# https://www.kaggle.com/datasets/ashok205/kaggriculture-top10-replay-archive
# https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-2026-09-26
# Place in: C:\Users\Sundareswaran\Kagriculture\research\v60\data\kaggle_downloads\
