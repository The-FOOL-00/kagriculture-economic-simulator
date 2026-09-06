import os
import glob

raw_dirs = glob.glob("replays/raw/*")
for d in raw_dirs:
    if os.path.isdir(d):
        files = glob.glob(f"{d}/**/*", recursive=True)
        files_only = [f for f in files if os.path.isfile(f)]
        total_sz = sum(os.path.getsize(f) for f in files_only)
        print(f"Directory: {d}")
        print(f"  Files: {len(files_only)} files | Total size: {round(total_sz/(1024*1024), 2)} MB")
        for f in files_only[:3]:
            print(f"    {os.path.basename(f)} ({round(os.path.getsize(f)/1024, 1)} KB)")
