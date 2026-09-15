import os
import re
import subprocess
import glob

CANDIDATE_RANGES = {
    "246000-246049": range(246000, 246050),
    "247000-247049": range(247000, 247050),
    "248000-248049": range(248000, 248050),
    "249000-249049": range(249000, 249050),
    "250000-250049": range(250000, 250050),
}

all_target_seeds = set()
for r in CANDIDATE_RANGES.values():
    all_target_seeds.update(r)

print(f"Total candidate seeds to audit: {len(all_target_seeds)}")

# 1. Search in git log
print("\n--- 1. Checking git commit messages and diffs ---")
git_cmd = ["git", "log", "-S", "246000", "--oneline"]
res = subprocess.run(git_cmd, capture_output=True, text=True)
print("git log -S 246000:", res.stdout.strip())

# Check all range prefixes in git log
for prefix in ["246", "247", "248", "249", "250"]:
    git_grep = subprocess.run(["git", "log", "--all", f"--grep={prefix}"], capture_output=True, text=True)
    if git_grep.stdout.strip():
        print(f"Found git commit with grep {prefix}: {git_grep.stdout.strip()[:200]}")
    else:
        print(f"No git commits mentioning {prefix}")

# 2. Check git log -G for regex
for prefix in ["2460", "2470", "2480", "2490", "2500"]:
    git_g = subprocess.run(["git", "log", "--all", "-G", prefix, "--oneline"], capture_output=True, text=True)
    if git_g.stdout.strip():
        print(f"Found git diffs containing {prefix}:\n{git_g.stdout.strip()[:300]}")
    else:
        print(f"Clean in git history diffs: {prefix}")

# 3. Check all files in workspace
print("\n--- 2. Checking all files in workspace ---")
findings = {k: [] for k in CANDIDATE_RANGES.keys()}

for root, dirs, files in os.walk("."):
    # skip .git objects to avoid binary noise, but we checked git log above
    if ".git" in root:
        continue
    for f in files:
        filepath = os.path.join(root, f)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                for rname, rrange in CANDIDATE_RANGES.items():
                    for seed in rrange:
                        s_str = str(seed)
                        if s_str in content:
                            findings[rname].append((filepath, s_str))
                            break
        except Exception as e:
            pass

for rname, hits in findings.items():
    print(f"Range {rname}: {len(hits)} occurrences found.")
    for h in hits[:5]:
        print(f"   {h[0]} contains {h[1]}")

# 4. Check transcripts and appDataDir
app_data = r"C:\Users\Sundareswaran\.gemini\antigravity-ide"
print(f"\n--- 3. Checking AppData / Transcripts at {app_data} ---")
appdata_hits = {k: [] for k in CANDIDATE_RANGES.keys()}
if os.path.exists(app_data):
    for root, dirs, files in os.walk(app_data):
        for f in files:
            if f.endswith((".jsonl", ".txt", ".md", ".json", ".log")):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                        for rname, rrange in CANDIDATE_RANGES.items():
                            for seed in rrange:
                                s_str = str(seed)
                                if s_str in content:
                                    appdata_hits[rname].append((filepath, s_str))
                                    break
                except Exception:
                    pass

for rname, hits in appdata_hits.items():
    print(f"AppData Range {rname}: {len(hits)} occurrences found.")
    for h in hits[:5]:
        print(f"   {h[0]} contains {h[1]}")
