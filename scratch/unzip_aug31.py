import zipfile
import os

zip_path = "replays/raw/kaggle_daily_aug31/kaggriculture-episodes-2026-08-31.zip"
out_dir = "replays/raw/kaggle_daily_aug31"

if os.path.exists(zip_path):
    print(f"Unzipping {zip_path} ({os.path.getsize(zip_path)} bytes)...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(out_dir)
    print("Unzip complete!")
    os.remove(zip_path)
    print("Removed zip file.")
