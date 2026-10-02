#!/usr/bin/env python3
"""V60 — Kaggle API dataset discovery for September 2026 kaggriculture episodes."""
import requests
import json
import os

# Load credentials
with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
user = creds['username']
key = creds['key']
auth = (user, key)
TIMEOUT = 20

print(f"Authenticated as: {user}")
print()

# Method 1: Search for daily datasets
search_urls = [
    "https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes-2026-09&maxSize=100",
    "https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes&maxSize=100",
    "https://www.kaggle.com/api/v1/datasets/list?ownerUser=kaggle&search=kaggriculture&maxSize=100",
    "https://www.kaggle.com/api/v1/datasets/list?ownerUser=georgymamarin&maxSize=100",
]

all_datasets = {}
for url in search_urls:
    try:
        r = requests.get(url, auth=auth, timeout=TIMEOUT)
        print(f"URL: {url}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Results: {len(data)}")
            for d in data:
                ref = d.get('ref', 'unknown')
                all_datasets[ref] = d
                size = d.get('totalBytes', 0)
                updated = d.get('lastUpdated', '?')
                print(f"  {ref} | {size} bytes | {updated}")
        else:
            print(f"  Body: {r.text[:200]}")
        print()
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {str(e)[:200]}")
        print()

print(f"\n=== TOTAL UNIQUE DATASETS FOUND: {len(all_datasets)} ===")

# Filter to September episode datasets
sep_datasets = {k: v for k, v in all_datasets.items() if '2026-09' in k and 'episode' in k.lower()}
print(f"September episode datasets: {len(sep_datasets)}")
for k in sorted(sep_datasets.keys()):
    print(f"  {k}")

# Save manifest
with open('research/v60/data/dataset_discovery.json', 'w') as f:
    json.dump({'all_datasets': list(all_datasets.keys()), 'sep_datasets': list(sep_datasets.keys())}, f, indent=2)
print("\nSaved to research/v60/data/dataset_discovery.json")
