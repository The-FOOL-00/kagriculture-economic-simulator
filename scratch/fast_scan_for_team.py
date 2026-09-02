import glob
import json
import os
import sys

sub_id = 55893176
team_id = 16657198

def fast_scan_directory(dir_path):
    files = glob.glob(os.path.join(dir_path, "*.json"))
    print(f"Scanning {len(files)} files in {dir_path}...", flush=True)
    matches = []
    
    sub_str = str(sub_id).encode("utf-8")
    team_str = str(team_id).encode("utf-8")
    
    for f in files:
        try:
            with open(f, "rb") as fp:
                # Read first 8KB which contains agents metadata
                header = fp.read(8192)
                if sub_str in header or team_str in header:
                    matches.append(f)
                    print(f"MATCH FOUND: {f}", flush=True)
        except Exception as e:
            pass
            
    print(f"Total matches in {dir_path}: {len(matches)}", flush=True)
    return matches

if __name__ == "__main__":
    for d in ["replays", "replays/raw/kaggle_daily_aug30", "replays/raw/kaggle_daily_aug31"]:
        if os.path.exists(d):
            fast_scan_directory(d)
