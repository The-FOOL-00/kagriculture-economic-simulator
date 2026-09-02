import glob
import json
import os
import sys

TARGET_STRINGS = [b"Sundareswaran", b"Rajaguru", b"Eldritch", b"thefool00"]

def scan_folder(dir_path):
    files = glob.glob(os.path.join(dir_path, "*.json"))
    print(f"Scanning {len(files)} JSON files in {dir_path}...", flush=True)
    matches = []
    
    for f in files:
        try:
            with open(f, "rb") as fp:
                # Read entire file or first 32KB
                content = fp.read(32768)
                if any(t in content for t in TARGET_STRINGS):
                    matches.append(f)
                    print(f"FOUND MATCH: {f}", flush=True)
        except Exception as e:
            pass
            
    print(f"Total matches in {dir_path}: {len(matches)}", flush=True)
    return matches

if __name__ == "__main__":
    total = []
    for d in ["replays", "replays/raw/kaggle_daily_aug30", "replays/raw/kaggle_daily_aug31"]:
        if os.path.exists(d):
            m = scan_folder(d)
            total.extend(m)
    print(f"TOTAL MATCHES ACROSS ALL FOLDERS: {len(total)}")
