import os
import sys
import subprocess
import glob
import re

CANDIDATES = [
    ("246000-246049", 246000, 246049),
    ("247000-247049", 247000, 247049),
    ("248000-248049", 248000, 248049),
    ("249000-249049", 249000, 249049),
    ("250000-250049", 250000, 250050),
]

print("=== FAST AUDIT OF CANDIDATE SEED RANGES ===", flush=True)

# 1. Git check
print("\n--- 1. Git History Check ---", flush=True)
for label, start, end in CANDIDATES:
    # Check commit log for string
    res = subprocess.run(["git", "log", "--all", f"--grep={start}"], capture_output=True, text=True)
    commits = res.stdout.strip()
    if commits:
        print(f"[{label}] Found in commit message: {commits[:100]}", flush=True)
    else:
        # Check pickaxe for start seed
        res_s = subprocess.run(["git", "log", "--all", "-S", str(start), "--oneline"], capture_output=True, text=True)
        if res_s.stdout.strip():
            print(f"[{label}] Found in git diff (-S {start}): {res_s.stdout.strip()}", flush=True)
        else:
            print(f"[{label}] Clean in git commit messages and diffs for {start}", flush=True)

# 2. Workspace check
print("\n--- 2. Workspace Files Check ---", flush=True)
workspace_dir = os.path.abspath(".")
extensions = {".py", ".json", ".csv", ".md", ".txt", ".sh", ".ps1"}

file_list = []
for root, dirs, files in os.walk(workspace_dir):
    if ".git" in root or ".gemini" in root:
        continue
    for f in files:
        if any(f.endswith(ext) for ext in extensions):
            file_list.append(os.path.join(root, f))

print(f"Scanning {len(file_list)} files in workspace...", flush=True)

range_hits = {c[0]: [] for c in CANDIDATES}

for fpath in file_list:
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
            for label, start, end in CANDIDATES:
                # Check prefix or seeds
                prefix = str(start)[:4] # e.g. "2460"
                if prefix in text:
                    # check exact seeds in range
                    for s in range(start, end + 1):
                        if str(s) in text:
                            range_hits[label].append((fpath, s))
                            break
    except Exception as e:
        pass

for label, hits in range_hits.items():
    if hits:
        print(f"[{label}] FOUND {len(hits)} occurrences in workspace:", flush=True)
        for h in hits[:5]:
            print(f"    {os.path.relpath(h[0], workspace_dir)}: seed {h[1]}", flush=True)
    else:
        print(f"[{label}] 100% CLEAN in all workspace files", flush=True)

# 3. Check stride / range expressions in python files
print("\n--- 3. Checking Stride / Range Formulas in .py files ---", flush=True)
py_files = [f for f in file_list if f.endswith(".py")]
range_pattern = re.compile(r'range\s*\(\s*(\d+)\s*,\s*(\d+)')
stride_pattern = re.compile(r'(\d+)\s*\+\s*i\s*\*\s*(\d+)')

stride_overlaps = {c[0]: [] for c in CANDIDATES}

for pyf in py_files:
    try:
        with open(pyf, "r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
            for line_idx, line in enumerate(lines, 1):
                # range check
                for m in range_pattern.finditer(line):
                    r_start, r_end = int(m.group(1)), int(m.group(2))
                    for label, start, end in CANDIDATES:
                        if not (r_end <= start or r_start > end):
                            stride_overlaps[label].append((os.path.relpath(pyf, workspace_dir), line_idx, f"range({r_start}, {r_end})"))
                # stride check
                for m in stride_pattern.finditer(line):
                    base, step = int(m.group(1)), int(m.group(2))
                    # check if any i gives value in candidate range
                    for label, start, end in CANDIDATES:
                        # base + i * step in [start, end]
                        if step > 0:
                            min_i = max(0, (start - base) // step)
                            for test_i in range(min_i, min_i + 150):
                                val = base + test_i * step
                                if start <= val <= end:
                                    stride_overlaps[label].append((os.path.relpath(pyf, workspace_dir), line_idx, f"{base} + i*{step} (i={test_i} -> {val})"))
                                    break
    except Exception:
        pass

for label, overlaps in stride_overlaps.items():
    if overlaps:
        print(f"[{label}] Stride/range overlap detected: {overlaps}", flush=True)
    else:
        print(f"[{label}] Zero range or stride arithmetic overlaps", flush=True)

# 4. Check conversation transcripts in appDataDir
print("\n--- 4. Checking conversation transcripts ---", flush=True)
transcripts = glob.glob(r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\*\.system_generated\logs\transcript.jsonl")
print(f"Found {len(transcripts)} transcripts to check...", flush=True)
transcript_hits = {c[0]: [] for c in CANDIDATES}
for tpath in transcripts:
    try:
        with open(tpath, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
            for label, start, end in CANDIDATES:
                prefix = str(start)[:4]
                if prefix in content:
                    for s in range(start, end + 1):
                        if str(s) in content:
                            transcript_hits[label].append((tpath, s))
                            break
    except Exception:
        pass

for label, hits in transcript_hits.items():
    if hits:
        print(f"[{label}] Found in transcripts: {hits}", flush=True)
    else:
        print(f"[{label}] 100% CLEAN in all agent transcripts", flush=True)

print("\n=== AUDIT FINISHED ===", flush=True)
