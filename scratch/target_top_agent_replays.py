import os
import glob
import json

def find_exact_files():
    all_files = glob.glob("**/*.json", recursive=True)
    targets = ["crop_dusta", "whyme", "yuan800", "kawatta", "mtn", "3junghoon", "yuyajk", "gayathri", "mrgs"]
    found = {}
    for f in all_files:
        low = f.lower().replace("\\", "/")
        for t in targets:
            if t in low:
                found.setdefault(t, []).append(f)
                
    for t, flist in found.items():
        print(f"Target '{t}': {len(flist)} files")
        for f in flist[:3]:
            print(f"  {f} ({round(os.path.getsize(f)/(1024*1024), 2)} MB)")

if __name__ == "__main__":
    find_exact_files()
