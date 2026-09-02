import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

# Download reference agents
ref_dir = "replays/raw/reference_agents"
os.makedirs(ref_dir, exist_ok=True)
print(f"Downloading raykkretzschmar/kaggriculture-reference-agents -> {ref_dir} ...")
try:
    api.dataset_download_files("raykkretzschmar/kaggriculture-reference-agents", path=ref_dir, unzip=True)
    print("Reference agents downloaded successfully! Files:", os.listdir(ref_dir))
except Exception as e:
    print(f"Ref agents error: {e}")

# Download benchmark matchups
bench_dir = "replays/raw/destbreso"
os.makedirs(bench_dir, exist_ok=True)
print(f"\nDownloading destbreso/kaggriculture-benchmark-matchups -> {bench_dir} ...")
try:
    api.dataset_download_files("destbreso/kaggriculture-benchmark-matchups", path=bench_dir, unzip=True)
    print("Benchmark matchups downloaded successfully! Files:", os.listdir(bench_dir))
except Exception as e:
    print(f"Benchmark error: {e}")
