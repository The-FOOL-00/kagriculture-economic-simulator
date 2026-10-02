#!/usr/bin/env python3
"""V60 — Probe correct Kaggle API URL patterns for dataset download."""
import requests
import json
import os

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 30

def try_url(label, url, stream=False):
    try:
        r = requests.get(url, auth=auth, timeout=TIMEOUT, stream=stream)
        ct = r.headers.get('content-type', '')
        print(f"  [{r.status_code}] {label}")
        print(f"    Content-Type: {ct}")
        if 'json' in ct and r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                print(f"    List length: {len(data)}")
                for item in data[:3]:
                    print(f"    Item: {str(item)[:120]}")
            elif isinstance(data, dict):
                keys = list(data.keys())
                print(f"    Dict keys: {keys}")
                for k in keys[:5]:
                    v = data[k]
                    print(f"    {k}: {str(v)[:80]}")
        elif r.status_code == 200:
            print(f"    Body (first 300): {r.text[:300]}")
        elif r.status_code != 404:
            print(f"    Error body: {r.text[:200]}")
        return r
    except Exception as e:
        print(f"  [ERR] {label}: {e}")
        return None

print("=== Probing Kaggle API patterns ===\n")

# 1. Direct dataset download URL
print("-- Pattern 1: Direct download --")
try_url("georgymamarin episodes download",
        "https://www.kaggle.com/api/v1/datasets/georgymamarin/kaggriculture-episodes/download")

# 2. List endpoint (this worked)
print("\n-- Pattern 2: List with search --")
try_url("search list",
        "https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes&maxSize=100")

# 3. Versions endpoint
print("\n-- Pattern 3: Versions --")
try_url("georgymamarin versions",
        "https://www.kaggle.com/api/v1/datasets/georgymamarin/kaggriculture-episodes/versions")

# 4. Files endpoint variations
print("\n-- Pattern 4: Files --")
try_url("georgymamarin files",
        "https://www.kaggle.com/api/v1/datasets/georgymamarin/kaggriculture-episodes/files")

# 5. The search result object has a 'ref' field - try using that
print("\n-- Pattern 5: Via ref from search result --")
r = requests.get("https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes&maxSize=100",
                 auth=auth, timeout=TIMEOUT)
if r.status_code == 200:
    datasets = r.json()
    for ds in datasets:
        ref = ds.get('ref', '')
        print(f"\n  Dataset ref: {ref}")
        print(f"  All fields: {list(ds.keys())}")
        print(f"  Full: {json.dumps(ds, indent=2)[:500]}")

# 6. kaggle index - try correct slug
print("\n-- Pattern 6: kaggle/kaggriculture-episodes-index --")
try_url("index files",
        "https://www.kaggle.com/api/v1/datasets/kaggle/kaggriculture-episodes-index/files")
try_url("index download",
        "https://www.kaggle.com/api/v1/datasets/kaggle/kaggriculture-episodes-index/download")

# 7. ashok205 dataset
print("\n-- Pattern 7: ashok205/kaggriculture-top10-replay-archive --")
try_url("ashok files",
        "https://www.kaggle.com/api/v1/datasets/ashok205/kaggriculture-top10-replay-archive/files")

# 8. Sep 26 daily dataset
print("\n-- Pattern 8: kaggle/kaggriculture-episodes-2026-09-26 --")
try_url("sep26 files",
        "https://www.kaggle.com/api/v1/datasets/kaggle/kaggriculture-episodes-2026-09-26/files")
try_url("sep26 download",
        "https://www.kaggle.com/api/v1/datasets/kaggle/kaggriculture-episodes-2026-09-26/download")
