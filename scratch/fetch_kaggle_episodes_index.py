import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

target_dir = "replays/raw/kaggle_index"
os.makedirs(target_dir, exist_ok=True)
print(f"Downloading kaggle/kaggriculture-episodes-index -> {target_dir} ...")
try:
    api.dataset_download_files("kaggle/kaggriculture-episodes-index", path=target_dir, unzip=True)
    print("Downloaded and unzipped successfully!")
    print("Files:", os.listdir(target_dir))
except Exception as e:
    print(f"Error: {e}")
