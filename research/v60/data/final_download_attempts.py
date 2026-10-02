#!/usr/bin/env python3
"""V60 — Try ALL remaining Kaggle download patterns.
The list API works, the download API returns 404 at /api/v1/datasets/{owner}/{name}/download
But the dataset URL (Kaggle public dataset page) exists. 
Try: direct GCS/blob download URLs embedded in dataset metadata.
"""
import requests
import json
import os
from pathlib import Path

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 30

OUT = Path("research/v60/data")
OUT.mkdir(parents=True, exist_ok=True)

# Load what we know about the datasets
with open('research/v60/data/full_dataset_list.json') as f:
    datasets = json.load(f)

print("=== APPROACH A: Use list API's embedded direct URLs ===")
for ds in datasets:
    ref = ds.get('ref', '?')
    url = ds.get('urlNullable') or ds.get('url', '')
    print(f"\n{ref}:")
    print(f"  url: {url}")
    print(f"  totalBytes: {ds.get('totalBytes', 0):,}")
    print(f"  version: {ds.get('currentVersionNumber', '?')}")

# Try to get the dataset download directly via the datasetUrl
print("\n=== APPROACH B: Try {datasetUrl}/download ===")
for ds in datasets:
    ref = ds.get('ref', '?')
    url = ds.get('urlNullable') or ds.get('url', '')
    if not url:
        continue
    
    download_url = url + "/download"
    try:
        r = requests.get(download_url, auth=auth, timeout=TIMEOUT, allow_redirects=False)
        print(f"  {ref}: {r.status_code}")
        if r.status_code in (301, 302, 307, 308):
            loc = r.headers.get('Location', '')
            print(f"    Redirect -> {loc[:150]}")
        elif r.status_code == 200:
            ct = r.headers.get('content-type', '')
            print(f"    Content-Type: {ct}, Size: {len(r.content)}")
    except Exception as e:
        print(f"  {ref}: ERROR {e}")

# Try new Kaggle API path format (v2/v3)
print("\n=== APPROACH C: Try newer API paths ===")
test_refs = [
    ("kaggle", "kaggriculture-episodes-index"),
    ("kaggle", "kaggriculture-episodes-2026-09-26"),
    ("ashok205", "kaggriculture-top10-replay-archive"),
]
for owner, name in test_refs:
    for path in [
        f"https://www.kaggle.com/api/v2/datasets/{owner}/{name}/versions/1/download",
        f"https://www.kaggle.com/datasets/{owner}/{name}/download?resource=download",
        f"https://www.kaggle.com/api/v1/datasets/{owner}/{name}/versions/1/files",
    ]:
        try:
            r = requests.get(path, auth=auth, timeout=TIMEOUT, allow_redirects=False)
            ct = r.headers.get('content-type', '')
            print(f"  [{r.status_code}] {path.split('kaggle.com')[-1][:80]}")
            if r.status_code == 200 and 'json' in ct:
                data = r.json()
                print(f"    JSON: {str(data)[:200]}")
            elif r.status_code in (301, 302, 307):
                print(f"    -> {r.headers.get('Location', '')[:100]}")
        except Exception as e:
            print(f"    ERROR: {e}")

# Try the Kaggle competition leaderboard to get submission IDs for top teams
print("\n=== APPROACH D: Competition leaderboard JSON ===")
for url in [
    "https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard?format=json&maxSize=100",
    "https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard",
]:
    r = requests.get(url, auth=auth, timeout=TIMEOUT)
    print(f"  {url}: {r.status_code}")
    ct = r.headers.get('content-type', '')
    if 'json' in ct and r.status_code == 200:
        data = r.json()
        print(f"  Type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        print(f"  Preview: {str(data)[:500]}")
        with open(OUT / 'leaderboard_api.json', 'w') as f:
            json.dump(data, f, indent=2)
    elif r.status_code == 200:
        print(f"  Body: {r.text[:300]}")

# Try to get submission episodes for top teams via their submission IDs
# The state.json had submission IDs - check if any are from Sep top teams
print("\n=== APPROACH E: Use georgymamarin state.json submissions ===")
with open('replays/raw/georgymamarin/state.json') as f:
    state = json.load(f)
subs = state.get('submissions', [])
print(f"Total submissions in state.json: {len(subs)}")
print(f"Last 5 submission IDs: {subs[-5:]}")
print(f"First 5 submission IDs: {subs[:5]}")

# Try to get episodes for the last submission ID
last_sub = subs[-1]
for ep_url in [
    f"https://www.kaggle.com/api/v1/competitions/episodes/{last_sub}",
    f"https://www.kaggle.com/api/v1/competitions/kaggriculture/episodes/{last_sub}",
]:
    r = requests.get(ep_url, auth=auth, timeout=TIMEOUT)
    print(f"  {ep_url}: {r.status_code}")
    ct = r.headers.get('content-type', '')
    if r.status_code == 200 and 'json' in ct:
        print(f"  {r.json()}")

# Check if the manifest.csv from kaggle_index still has Sep dates
print("\n=== APPROACH F: Check kaggle_index manifest for September ===")
manifest_path = "replays/raw/kaggle_index/manifest.csv"
if os.path.exists(manifest_path):
    import csv
    with open(manifest_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"Manifest rows: {len(rows)}")
    print(f"Columns: {list(rows[0].keys()) if rows else 'none'}")
    # Show last 10 entries (most recent dates)
    for row in rows[-10:]:
        print(f"  {row}")
