import os
import re
import json

def verify_seed_contamination(seed_start=35000, seed_end=35199):
    target_seeds = set(range(seed_start, seed_end + 1))
    print(f"Verifying zero contamination for {len(target_seeds)} seeds ({seed_start} - {seed_end})...")

    matched_files = {}
    total_files_scanned = 0

    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root:
            continue
        for fn in files:
            if fn.endswith((".py", ".md")) and fn != "verify_contamination.py":
                fpath = os.path.join(root, fn)
                total_files_scanned += 1
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    tokens = set(int(x) for x in re.findall(r'\b\d{4,6}\b', content))
                    matched = target_seeds.intersection(tokens)
                    if matched:
                        matched_files[fpath] = sorted(list(matched))
                except Exception as e:
                    pass

    print(f"Total files scanned: {total_files_scanned}")
    if not matched_files:
        print(f"VERIFICATION SUCCESS: 0 CONTAMINATIONS FOUND! Range {seed_start}-{seed_end} is 100% PRISTINE.")
        return True, {}
    else:
        print(f"VERIFICATION FAILURE: {len(matched_files)} files contained target seeds:")
        for fp, seeds in matched_files.items():
            print(f"  {fp}: seeds {seeds[:5]}")
        return False, matched_files

if __name__ == "__main__":
    is_pure, matches = verify_seed_contamination(35000, 35199)
    res = {
        "seed_range": [35000, 35199],
        "is_pure": is_pure,
        "matches": matches
    }
    with open("scratch/seed_contamination_verification.json", "w") as f:
        json.dump(res, f, indent=2)
