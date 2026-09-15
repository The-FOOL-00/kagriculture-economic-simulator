import os
import re
import sys
import json
from pathlib import Path

CANDIDATES = {
    "60000-60049": set(range(60000, 60050)),
    "70000-70049": set(range(70000, 70050)),
    "80000-80049": set(range(80000, 80050)),
    "90000-90049": set(range(90000, 90050)),
    "100000-100049": set(range(100000, 100050)),
}

ALL_CANDIDATE_SEEDS = set.union(*CANDIDATES.values())

ROOT_DIR = Path(".").resolve()
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", "kagsim.egg-info", "temporary"}

all_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for f in files:
        if f.endswith((".pyd", ".zip", ".tar", ".gz", ".png", ".jpg", ".exe", ".dll")):
            continue
        all_files.append(Path(root) / f)

print(f"Total workspace files to scan: {len(all_files)}", flush=True)

# Also collect brain transcripts
brain_dir = Path(r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain")
brain_files = []
if brain_dir.exists():
    for f in brain_dir.glob("*/.system_generated/logs/transcript*.jsonl"):
        brain_files.append(f)
print(f"Total brain transcript files: {len(brain_files)}", flush=True)

range_regex = re.compile(r"range\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")
stride_regex = re.compile(r"(\d+)\s*\+\s*i\s*\*\s*(\d+)")
num_regex = re.compile(r"\b\d{5,6}\b")

results = {name: [] for name in CANDIDATES}

for p in all_files + brain_files:
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
        
    rel_p = str(p.relative_to(ROOT_DIR)) if str(p).startswith(str(ROOT_DIR)) else str(p)
    
    # 1. Range overlap check
    for m in range_regex.finditer(content):
        start_r, end_r = int(m.group(1)), int(m.group(2))
        for cname, cset in CANDIDATES.items():
            c_start, c_end = min(cset), max(cset) + 1
            if max(start_r, c_start) < min(end_r, c_end):
                results[cname].append({
                    "file": rel_p,
                    "type": "range_overlap",
                    "detail": f"range({start_r}, {end_r}) overlaps {cname}",
                    "matched_text": m.group(0)
                })

    # 2. Stride overlap check
    for m in stride_regex.finditer(content):
        base, stride = int(m.group(1)), int(m.group(2))
        # check up to 500 terms
        for i in range(500):
            val = base + i * stride
            if val in ALL_CANDIDATE_SEEDS:
                for cname, cset in CANDIDATES.items():
                    if val in cset:
                        results[cname].append({
                            "file": rel_p,
                            "type": "stride_overlap",
                            "detail": f"{base} + i * {stride} hit seed {val} (i={i})",
                            "matched_text": m.group(0)
                        })

    # 3. Individual seeds via set intersection
    raw_nums = set(int(x) for x in num_regex.findall(content))
    hits = raw_nums.intersection(ALL_CANDIDATE_SEEDS)
    if hits:
        lines = content.splitlines()
        for seed in hits:
            # find line number
            seed_str = str(seed)
            for l_idx, line in enumerate(lines, 1):
                if re.search(rf"\b{seed_str}\b", line):
                    for cname, cset in CANDIDATES.items():
                        if seed in cset:
                            results[cname].append({
                                "file": rel_p,
                                "type": "individual_seed",
                                "seed": seed,
                                "line": l_idx,
                                "line_text": line.strip()[:140]
                            })

print("\n" + "="*80, flush=True)
print("COMPREHENSIVE PROVENANCE AUDIT RESULTS", flush=True)
print("="*80, flush=True)

summary_rows = []

for cname, hits in results.items():
    print(f"\n=======================================================", flush=True)
    print(f"CANDIDATE RANGE: {cname} (Total Hits: {len(hits)})", flush=True)
    print(f"=======================================================", flush=True)
    if not hits:
        print("  >>> ZERO HITS! 100% PRISTINE / VIRGIN! <<<", flush=True)
        summary_rows.append((cname, 0, 0, 0, "None", "VIRGIN"))
    else:
        # Categorize hits
        individual_hits = [h for h in hits if h["type"] == "individual_seed"]
        range_hits = [h for h in hits if h["type"] in ("range_overlap", "stride_overlap")]
        
        # Check files
        by_file = {}
        for h in hits:
            by_file.setdefault(h["file"], []).append(h)
            
        print(f"  Files with hits: {len(by_file)}")
        for f, fhits in by_file.items():
            print(f"  --- File: {f} ({len(fhits)} hits) ---")
            for h in fhits[:5]:
                if h["type"] == "individual_seed":
                    print(f"    Line {h['line']}: [Seed {h['seed']}] {h['line_text']}")
                else:
                    print(f"    {h['type']}: {h['detail']} -> `{h['matched_text']}`")
            if len(fhits) > 5:
                print(f"    ... and {len(fhits) - 5} more hits in this file.")
                
        # Determine status
        # If any hits in simulation scripts or result json/csv -> CONTAMINATED
        status = "CONTAMINATED" if range_hits or individual_hits else "VIRGIN"
        summary_rows.append((cname, len(individual_hits), len(range_hits), len(by_file), "Historical Script/Run", status))

print("\n\n" + "="*80, flush=True)
print("AUDIT SUMMARY TABLE", flush=True)
print("="*80, flush=True)
print(f"| {'Candidate Range':<16} | {'Individual Hits':<16} | {'Range Overlaps':<16} | {'Files Affected':<16} | {'Status':<12} |")
print(f"|{'-'*18}|{'-'*18}|{'-'*18}|{'-'*18}|{'-'*14}|")
for row in summary_rows:
    print(f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<16} | {row[3]:<16} | {row[5]:<12} |")

