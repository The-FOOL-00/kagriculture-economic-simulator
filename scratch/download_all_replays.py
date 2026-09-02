import os
import sys
import json
from kaggle.api.kaggle_api_extended import KaggleApi

# Ensure UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

datasets_to_download = [
    ("georgymamarin/kaggriculture-episodes", "replays/raw/georgymamarin"),
    ("kaggle/kaggriculture-episodes-index", "replays/raw/kaggle_index"),
    ("destbreso/kaggriculture-benchmark-matchups", "replays/raw/destbreso"),
    ("raykkretzschmar/kaggriculture-reference-agents", "replays/raw/reference_agents"),
    ("vijaikm/kaggriculture-match-replay-corpus", "replays/raw/vijaikm")
]

for ds, target_dir in datasets_to_download:
    print(f"\n==========================================")
    print(f"Downloading dataset: {ds} -> {target_dir}")
    print(f"==========================================")
    os.makedirs(target_dir, exist_ok=True)
    try:
        api.dataset_download_files(ds, path=target_dir, unzip=True)
        print(f"Successfully downloaded and unzipped {ds}")
        files = os.listdir(target_dir)
        print(f"Contents ({len(files)} files/dirs): {files[:10]}")
    except Exception as e:
        print(f"Error downloading {ds}: {e}")

print("\nAll downloads finished!")
