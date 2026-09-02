import zipfile
import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

zip_path = "replays/raw/georgymamarin/kaggriculture-episodes.zip"
print(f"Opening zip: {zip_path} (Size: {os.path.getsize(zip_path)/1024/1024:.1f} MB)")

with zipfile.ZipFile(zip_path, 'r') as z:
    file_list = z.namelist()
    print(f"Total files in zip: {len(file_list)}")
    print("Sample 20 files:")
    for f in file_list[:20]:
        print(f"  {f}")
    
    # Check if there are csv index files or directories
    csvs = [f for f in file_list if f.endswith('.csv')]
    jsons = [f for f in file_list if f.endswith('.json')]
    print(f"CSVs: {len(csvs)}, JSONs: {len(jsons)}")
    if csvs:
        print(f"CSV files: {csvs}")
