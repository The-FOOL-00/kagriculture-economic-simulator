#!/usr/bin/env python3
"""V60 — Discover correct Kaggle download URL and retrieve episode index.
Uses the Kaggle v1 download API with proper path construction.
"""
import requests
import json
import os
import urllib.parse

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 60

os.makedirs('research/v60/data', exist_ok=True)

def try_download(label, url, save_path=None, max_bytes=None):
    """Try to download a URL. Returns (success, content_type, size)."""
    try:
        r = requests.get(url, auth=auth, timeout=TIMEOUT, stream=True, 
                        allow_redirects=True)
        ct = r.headers.get('content-type', '')
        cl = r.headers.get('content-length', 'unknown')
        print(f"  [{r.status_code}] {label}")
        print(f"    Content-Type: {ct}")
        print(f"    Content-Length: {cl}")
        print(f"    Final URL: {r.url[:120]}")
        
        if r.status_code == 200:
            content = b""
            for chunk in r.iter_content(chunk_size=65536):
                content += chunk
                if max_bytes and len(content) >= max_bytes:
                    break
            print(f"    Downloaded: {len(content):,} bytes")
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(content)
                print(f"    Saved to: {save_path}")
            # Show content preview
            if 'json' in ct or save_path and save_path.endswith('.json'):
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        print(f"    JSON keys: {list(data.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"    JSON list length: {len(data)}")
                        if len(data) > 0:
                            print(f"    First item: {str(data[0])[:200]}")
                except:
                    print(f"    Body preview: {content[:300]}")
            elif b'PK' == content[:2]:
                print(f"    *** ZIP FILE DETECTED ***")
            elif content[:3] == b'\x1f\x8b\x08':
                print(f"    *** GZIP FILE DETECTED ***")
            else:
                print(f"    Preview: {content[:200]}")
            return True, ct, len(content), content
        elif r.status_code != 404:
            content = r.content
            print(f"    Error preview: {content[:300]}")
        return False, ct, 0, b""
    except Exception as e:
        print(f"  [ERR] {label}: {type(e).__name__}: {str(e)[:200]}")
        return False, '', 0, b""

print("=== Testing download URL patterns ===\n")

# Pattern A: /api/v1/datasets/{owner}/{name}/download/{filename}
# Pattern B: /api/v1/datasets/{owner}/{name}/download  (direct zip)
# Pattern C: /api/v1/datasets/{owner}/{name}/versions/{n}/download/{filename}
# Pattern D: /datasets/{owner}/{name}/download/{filename} (no api/v1)

BASE = "https://www.kaggle.com"

# --- Try to get the episodes INDEX (2KB file - small, safe to download) ---
print("--- kaggle/kaggriculture-episodes-index ---")

for pattern in [
    f"{BASE}/api/v1/datasets/kaggle/kaggriculture-episodes-index/download",
    f"{BASE}/api/v1/datasets/kaggle/kaggriculture-episodes-index/download/manifest.csv",
    f"{BASE}/api/v1/datasets/kaggle/kaggriculture-episodes-index/download/index.csv",
    f"{BASE}/api/v1/datasets/kaggle/kaggriculture-episodes-index/download/kaggriculture-episodes-index.zip",
    f"{BASE}/datasets/kaggle/kaggriculture-episodes-index/download/manifest.csv?datasetVersionNumber=60",
]:
    ok, ct, size, content = try_download(pattern.split('/')[-1], pattern, max_bytes=100000)
    if ok and size > 0 and size < 50000:
        # Save it
        fname = 'research/v60/data/episodes_index_' + pattern.split('/')[-1].replace('?', '_')
        with open(fname, 'wb') as f:
            f.write(content)
        print(f"  ==> SAVED: {fname}")
    print()

# --- Try ashok205 dataset (top-10 replays) file listing ---
print("\n--- ashok205/kaggriculture-top10-replay-archive ---")
for pattern in [
    f"{BASE}/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/download",
    f"{BASE}/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/download/README.md",
    f"{BASE}/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/download/top10_replays.csv",
    f"{BASE}/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/download/manifest.json",
    f"{BASE}/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/download/index.json",
]:
    ok, ct, size, content = try_download(pattern.split('/')[-1], pattern, max_bytes=200000)
    if ok and size > 0:
        fname = 'research/v60/data/ashok_' + urllib.parse.quote(pattern.split('/')[-1], safe='')
        with open(fname, 'wb') as f:
            f.write(content)
        print(f"  ==> SAVED: {fname}")
    print()

# --- Try georgymamarin updated dataset --- 
print("\n--- georgymamarin/kaggriculture-episodes (v77, updated today) ---")
for fname_try in ['daily_stats.csv', 'teams.csv', 'manifest.csv', 'README.md', 'state.json']:
    ok, ct, size, content = try_download(
        fname_try,
        f"{BASE}/api/v1/datasets/georgymamarin/kaggriculture-episodes/download/{fname_try}",
        max_bytes=500000
    )
    if ok and size > 0:
        save_path = f'research/v60/data/georgymamarin_{fname_try}'
        with open(save_path, 'wb') as f:
            f.write(content)
        print(f"  ==> SAVED: {save_path}")
    print()
