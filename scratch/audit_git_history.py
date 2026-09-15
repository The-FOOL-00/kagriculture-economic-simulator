import subprocess
import re

CANDIDATES = {
    "60000-60049": range(60000, 60050),
    "70000-70049": range(70000, 70050),
    "80000-80049": range(80000, 80050),
    "90000-90049": range(90000, 90050),
    "100000-100049": range(100000, 100050),
}

# Get list of all commit hashes
res = subprocess.run(["git", "log", "--format=%H %s"], capture_output=True, text=True, check=True)
commits = [line.split(" ", 1) for line in res.stdout.strip().splitlines() if line]

print(f"Total commits in history: {len(commits)}")

# We can search git log with -S for ranges and individual seeds
# To be fast and thorough, let's search for "600", "700", "800", "900", "1000"
for cname, crange in CANDIDATES.items():
    prefix = str(crange.start)[:3]
    print(f"\n--- Checking Git history for {cname} (prefix {prefix}) ---")
    
    # Check git log -S prefix
    cmd = ["git", "log", f"-S{prefix}", "--oneline"]
    res_s = subprocess.run(cmd, capture_output=True, text=True)
    if res_s.stdout.strip():
        # Found commits containing prefix, inspect diffs of those commits
        matching_commits = [l.split()[0] for l in res_s.stdout.strip().splitlines()]
        print(f"  Commits touching prefix '{prefix}': {len(matching_commits)}")
        for chash in matching_commits:
            diff_res = subprocess.run(["git", "show", chash], capture_output=True, text=True, errors="ignore")
            diff_text = diff_res.stdout
            
            # Check individual seeds
            for s in crange:
                s_str = str(s)
                if re.search(rf"(?<!\d){s_str}(?!\d)", diff_text):
                    print(f"  [Commit {chash[:8]}] matched individual seed {s}!")
            
            # Check range(..., ...)
            for m in re.finditer(r"range\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", diff_text):
                r_start, r_end = int(m.group(1)), int(m.group(2))
                if max(r_start, crange.start) < min(r_end, crange.stop):
                    print(f"  [Commit {chash[:8]}] matched range({r_start}, {r_end}) overlapping {cname}!")
    else:
        print(f"  No commits in git history contain prefix '{prefix}'. Clean!")
