#!/usr/bin/env python3
"""V60 — Extract file lists from list API response and discover download URLs.
The list endpoint returns full dataset metadata including files and versions.
"""
import requests
import json
import os

with open('C:/Users/Sundareswaran/.kaggle/kaggle.json') as f:
    creds = json.load(f)
auth = (creds['username'], creds['key'])
TIMEOUT = 30

# Get full dataset objects from list endpoint
r = requests.get(
    "https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes&maxSize=100",
    auth=auth, timeout=TIMEOUT
)
datasets = r.json()
print(f"Found {len(datasets)} datasets")

# Save full response
os.makedirs('research/v60/data', exist_ok=True)
with open('research/v60/data/full_dataset_list.json', 'w') as f:
    json.dump(datasets, f, indent=2)
print("Saved full_dataset_list.json")

# Extract files and versions from each
for ds in datasets:
    ref = ds.get('ref', 'unknown')
    title = ds.get('titleNullable', '?')
    ver = ds.get('currentVersionNumber', ds.get('currentVersionNumberNullable', 1))
    total_bytes = ds.get('totalBytes', ds.get('totalBytesNullable', 0))
    url = ds.get('url', ds.get('urlNullable', ''))
    updated = ds.get('lastUpdated', '?')
    
    print(f"\n{'='*60}")
    print(f"REF: {ref}")
    print(f"Title: {title}")
    print(f"Version: {ver}")
    print(f"Total bytes: {total_bytes:,}")
    print(f"URL: {url}")
    print(f"Updated: {updated}")
    
    # Files embedded in list response
    files = ds.get('files', [])
    print(f"Files embedded: {len(files)}")
    for fi in files[:10]:
        print(f"  {fi}")
    
    # Versions embedded
    versions = ds.get('versions', [])
    print(f"Versions embedded: {len(versions)}")
    for vi in versions[:3]:
        print(f"  {vi}")

# Now try to find correct download patterns using the Kaggle Python package directly
print("\n\n=== Trying kaggle Python package directly ===")
try:
    import kaggle
    from kaggle.api.kaggle_api_extended import KaggleApiExtended
    api = KaggleApiExtended()
    api.authenticate()
    print("Authenticated via kaggle package")
    
    # List files in a dataset
    for ref in ['kaggle/kaggriculture-episodes-index', 
                'kaggle/kaggriculture-episodes-2026-09-26',
                'ashok205/kaggriculture-top10-replay-archive']:
        owner, name = ref.split('/')
        try:
            files = api.dataset_list_files(owner + '/' + name)
            print(f"\nFiles in {ref}:")
            if hasattr(files, 'files'):
                for f in files.files[:10]:
                    print(f"  {f}")
            else:
                print(f"  Response: {files}")
        except Exception as e:
            print(f"  Error listing {ref}: {e}")
            
except Exception as e:
    print(f"kaggle package error: {e}")
