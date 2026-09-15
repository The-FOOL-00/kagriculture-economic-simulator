import os
import re
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Generate grid of candidate 50-seed blocks:
# E.g. start at 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 
# 105000, 115000, 125000, 135000, 145000, 155000, 165000, 175000, 185000, 
# 195000, 205000, 215000, 225000, 235000, 245000, 255000
BLOCKS = {}
for start in [
    60000, 70000, 80000, 85000, 95000, 105000, 115000, 125000, 135000, 
    145000, 155000, 165000, 175000, 185000, 195000, 205000, 215000, 225000,
    235000, 245000, 255000, 300000, 400000, 500000
]:
    BLOCKS[f"{start}-{start+49}"] = set(range(start, start + 50))

ALL_SEEDS = set.union(*BLOCKS.values())

ROOT_DIR = Path(".").resolve()
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", "kagsim.egg-info", "temporary"}

all_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for f in files:
        if f.endswith((".pyd", ".zip", ".tar", ".gz", ".png", ".jpg", ".exe", ".dll")):
            continue
        all_files.append(Path(root) / f)

print(f"Scanning {len(all_files)} workspace files for candidate blocks...", flush=True)

range_regex = re.compile(r"range\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")
stride_regex = re.compile(r"(\d+)\s*\+\s*i\s*\*\s*(\d+)")
num_regex = re.compile(r"\b\d{5,7}\b")

# Also collect any seed-specific patterns: e.g. "seed": 12345 or seed=12345 or Game(12345)
seed_context_regex = re.compile(r"(?:seed\s*[:=]\s*|\bGame\s*\(\s*|\bseeds?\s*=\s*\[?|start_seed\s*=\s*)(\d+)", re.IGNORECASE)

# Track:
# 1) seed_in_code: appeared in code/scripts/results as an actual seed
# 2) range_overlap: encloses or overlaps with candidate
# 3) stride_overlap: arithmetic progression hits candidate
# 4) any_number_match: raw number match (including replay money, leaderboards, etc.)

block_stats = {b: {
    "seed_in_code": [],
    "range_overlap": [],
    "stride_overlap": [],
    "any_number_files": set(),
} for b in BLOCKS}

for p in all_files:
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
        
    rel_p = str(p.relative_to(ROOT_DIR))
    
    # Range check
    for m in range_regex.finditer(content):
        s_r, e_r = int(m.group(1)), int(m.group(2))
        for bname, bset in BLOCKS.items():
            b_s, b_e = min(bset), max(bset) + 1
            if max(s_r, b_s) < min(e_r, b_e):
                block_stats[bname]["range_overlap"].append((rel_p, m.group(0)))
                
    # Stride check
    for m in stride_regex.finditer(content):
        base, stride = int(m.group(1)), int(m.group(2))
        for i in range(500):
            val = base + i * stride
            if val in ALL_SEEDS:
                for bname, bset in BLOCKS.items():
                    if val in bset:
                        block_stats[bname]["stride_overlap"].append((rel_p, m.group(0), val, i))
                        
    # Seed context check (explicit seed parameter)
    for m in seed_context_regex.finditer(content):
        s_val = int(m.group(1))
        if s_val in ALL_SEEDS:
            for bname, bset in BLOCKS.items():
                if s_val in bset:
                    block_stats[bname]["seed_in_code"].append((rel_p, m.group(0), s_val))
                    
    # Raw number match
    raw_nums = set(int(x) for x in num_regex.findall(content))
    hits = raw_nums.intersection(ALL_SEEDS)
    if hits:
        for val in hits:
            for bname, bset in BLOCKS.items():
                if val in bset:
                    block_stats[bname]["any_number_files"].add(rel_p)

print("\n" + "="*80)
print("CANDIDATE BLOCKS SCREENING RESULTS")
print("="*80)

clean_blocks = []

for bname, s in block_stats.items():
    n_seed = len(s["seed_in_code"])
    n_range = len(s["range_overlap"])
    n_stride = len(s["stride_overlap"])
    n_files = len(s["any_number_files"])
    
    # Filter out our own audit scripts from any_number_files
    actual_files = [f for f in s["any_number_files"] if not f.startswith("scratch\\audit_") and not f.startswith("scratch/audit_")]
    
    is_clean = (n_seed == 0 and n_range == 0 and n_stride == 0 and len(actual_files) == 0)
    
    print(f"\nBlock: {bname:<16} | Explicit Seed Hits: {n_seed:<3} | Ranges: {n_range:<3} | Strides: {n_stride:<3} | Non-Audit Files: {len(actual_files):<3}")
    if is_clean:
        print(f"  ===> 100% PRISTINE / ZERO HITS ACROSS ENTIRE REPOSITORY! <===")
        clean_blocks.append(bname)
    else:
        if n_seed > 0:
            print(f"  Explicit seed refs: {s['seed_in_code'][:2]}")
        if n_range > 0:
            print(f"  Range overlaps: {s['range_overlap'][:2]}")
        if n_stride > 0:
            print(f"  Stride overlaps: {s['stride_overlap'][:2]}")
        if actual_files:
            print(f"  Files with number match: {actual_files[:3]}")

print("\n" + "="*80)
print(f"ALL 100% PRISTINE CANDIDATE BLOCKS ({len(clean_blocks)} found):")
print(clean_blocks)
print("="*80)

