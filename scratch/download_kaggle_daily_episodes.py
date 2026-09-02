import os
import subprocess
import zipfile

os.makedirs("replays/raw/kaggle_daily_aug30", exist_ok=True)
os.makedirs("replays/raw/kaggle_daily_aug31", exist_ok=True)

print("Downloading kaggle/kaggriculture-episodes-2026-08-30...")
subprocess.run(["kaggle", "datasets", "download", "-d", "kaggle/kaggriculture-episodes-2026-08-30", "-p", "replays/raw/kaggle_daily_aug30", "--unzip"], check=True)
print("Finished downloading 2026-08-30!")

print("Downloading kaggle/kaggriculture-episodes-2026-08-31...")
subprocess.run(["kaggle", "datasets", "download", "-d", "kaggle/kaggriculture-episodes-2026-08-31", "-p", "replays/raw/kaggle_daily_aug31", "--unzip"], check=True)
print("Finished downloading 2026-08-31!")
