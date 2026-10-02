#!/usr/bin/env python3
"""V60 — Deep inspection of discovered datasets to find September replay data.
Priority targets:
1. kaggle/kaggriculture-episodes-index  (updated today - has manifest of all dates)
2. ashok205/kaggriculture-top10-replay-archive  (3.96 GB - TOP 10 replays!)
3. xishengfeng/kaggriculture-replay-db  (2.08 GB - replay DB)
4. kaggle/kaggriculture-episodes-2026-09-26  (Sep 26 daily)
5. georgymamarin/kaggriculture-episodes  (updated today)
"""
import requests
import json
import os

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 20

DATASETS = [
    "kaggle/kaggriculture-episodes-index",
    "ashok205/kaggriculture-top10-replay-archive",
    "xishengfeng/kaggriculture-replay-db",
    "kaggle/kaggriculture-episodes-2026-09-26",
    "georgymamarin/kaggriculture-episodes",
]

results = {}

for ds in DATASETS:
    owner, name = ds.split('/')
    print(f"\n{'='*60}")
    print(f"DATASET: {ds}")
    print(f"{'='*60}")

    # Get dataset metadata
    meta_url = f"https://www.kaggle.com/api/v1/datasets/{owner}/{name}"
    try:
        r = requests.get(meta_url, auth=auth, timeout=TIMEOUT)
        print(f"Metadata status: {r.status_code}")
        if r.status_code == 200:
            meta = r.json()
            print(f"  Title: {meta.get('title', '?')}")
            print(f"  Subtitle: {meta.get('subtitle', '?')}")
            print(f"  Total bytes: {meta.get('totalBytes', 0):,}")
            print(f"  Last updated: {meta.get('lastUpdated', '?')}")
            print(f"  Download count: {meta.get('downloadCount', '?')}")
            print(f"  Version: {meta.get('currentDatasetVersionNumber', '?')}")
            results[ds] = {'meta': meta}
        else:
            print(f"  Error: {r.text[:200]}")
            results[ds] = {'error': r.text[:200]}
    except Exception as e:
        print(f"  Exception: {e}")
        results[ds] = {'exception': str(e)}

    # Get file list
    files_url = f"https://www.kaggle.com/api/v1/datasets/{owner}/{name}/versions/{{ver}}/files"
    # Try version 1 and latest
    for ver in [1, meta.get('currentDatasetVersionNumber', 1) if 'meta' in results.get(ds, {}) else 1]:
        files_url_v = f"https://www.kaggle.com/api/v1/datasets/{owner}/{name}/versions/{ver}/files"
        try:
            r2 = requests.get(files_url_v, auth=auth, timeout=TIMEOUT)
            if r2.status_code == 200:
                fdata = r2.json()
                files = fdata.get('datasetFiles', fdata.get('files', []))
                print(f"\n  Files (ver {ver}): {len(files)}")
                for f in files[:20]:
                    fname = f.get('name', f.get('fileName', '?'))
                    fsize = f.get('totalBytes', f.get('fileSize', 0))
                    print(f"    {fname} | {fsize:,} bytes")
                if len(files) > 20:
                    print(f"    ... and {len(files)-20} more")
                if ds not in results:
                    results[ds] = {}
                results[ds]['files'] = [{'name': f.get('name', '?'), 'size': f.get('totalBytes', 0)} for f in files]
                break
            else:
                print(f"  Files (ver {ver}): status {r2.status_code}")
        except Exception as e:
            print(f"  Files exception: {e}")

# Save results
os.makedirs('research/v60/data', exist_ok=True)
with open('research/v60/data/dataset_inspection.json', 'w') as f:
    # Make serializable
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean(v) for v in obj]
        try:
            json.dumps(obj)
            return obj
        except:
            return str(obj)
    json.dump(clean(results), f, indent=2)

print(f"\n\nSaved to research/v60/data/dataset_inspection.json")
