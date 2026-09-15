import os
import re
import sys
import json
import glob
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(".").resolve()
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", "kagsim.egg-info", "temporary"}

# 1. Collect all execution ranges and explicit seed sets from simulation scripts
executed_seed_sets = set()
executed_ranges = []
script_evidence = {}

range_pattern = re.compile(r"range\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")
stride_pattern = re.compile(r"\[\s*(\d+)\s*\+\s*i\s*\*\s*(\d+)\s+for\s+i\s+in\s+range\s*\(\s*(\d+)\s*\)\s*\]")
seed_list_pattern = re.compile(r"(?:seeds?|SEEDS?|holdout|HOLDOUT|qual|QUAL|discovery|DISCOVERY)\s*=\s*\[([0-9,\s]+)\]")

py_files = [p for p in ROOT_DIR.rglob("*.py") if not any(part in IGNORE_DIRS for part in p.parts)]

for p in py_files:
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
        
    rel_p = str(p.relative_to(ROOT_DIR))
    if rel_p.startswith("scratch\\audit_") or rel_p.startswith("scratch/audit_"):
        continue
    if "find_virgin_candidates" in rel_p or "extract_all_executed" in rel_p:
        continue
        
    # Check if this script simulates or references seeds
    has_sim = ("kagsim" in content or "Game(" in content or "run_episode" in content or "run_scan" in content 
               or "run_paired" in content or "evaluate_pairing" in content or "seeds" in content.lower())
    if not has_sim:
        continue
        
    # Strides
    for m in stride_pattern.finditer(content):
        base, stride, count = int(m.group(1)), int(m.group(2)), int(m.group(3))
        seeds = [base + i * stride for i in range(count)]
        for s in seeds:
            executed_seed_sets.add(s)
            script_evidence.setdefault(s, []).append((rel_p, f"stride {base} + i*{stride} (count {count})"))
            
    # Ranges
    for m in range_pattern.finditer(content):
        start_r, end_r = int(m.group(1)), int(m.group(2))
        # Filter out trivial ranges like range(10) or range(720)
        if start_r >= 1000 or end_r >= 1000:
            executed_ranges.append((start_r, end_r, rel_p))
            # If range is reasonable size (<= 5000), add to set
            if end_r - start_r <= 5000:
                for s in range(start_r, end_r):
                    executed_seed_sets.add(s)
                    script_evidence.setdefault(s, []).append((rel_p, f"range({start_r}, {end_r})"))

    # Seed lists
    for m in seed_list_pattern.finditer(content):
        nums_str = m.group(1)
        nums = [int(x.strip()) for x in nums_str.split(",") if x.strip().isdigit()]
        for s in nums:
            if s >= 1000:
                executed_seed_sets.add(s)
                script_evidence.setdefault(s, []).append((rel_p, f"seed list in {m.group(0)[:40]}"))

print(f"Total explicitly executed / evaluated seeds found in scripts: {len(executed_seed_sets)}")
print(f"Total execution ranges recorded: {len(executed_ranges)}")

# 2. Extract all seeds from result artifacts (.json, .csv)
result_seeds = set()
result_evidence = {}

result_files = [p for p in ROOT_DIR.rglob("*") if p.suffix in (".json", ".csv") and not any(part in IGNORE_DIRS for part in p.parts)]

for p in result_files:
    rel_p = str(p.relative_to(ROOT_DIR))
    if rel_p.startswith("scratch\\audit_") or "find_virgin_candidates" in rel_p or "extract_all" in rel_p:
        continue
    # Skip raw Kaggle leaderboard CSVs or massive external replay CSVs that contain team ids / episode ids
    if "leaderboard_csv" in rel_p or "replays\\raw" in rel_p or "replays/raw" in rel_p:
        continue
        
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
        
    # Check for "seed": 12345 or {"seed": 12345}
    for m in re.finditer(r'["\']seed["\']\s*:\s*(\d+)', content):
        s = int(m.group(1))
        if s >= 1000:
            result_seeds.add(s)
            result_evidence.setdefault(s, []).append((rel_p, f'"seed": {s}'))
            
    # Check CSV header for "seed"
    if p.suffix == ".csv":
        lines = content.splitlines()
        if lines:
            header = [h.strip().lower() for h in lines[0].split(",")]
            if "seed" in header:
                idx = header.index("seed")
                for line in lines[1:]:
                    parts = line.split(",")
                    if len(parts) > idx and parts[idx].strip().isdigit():
                        s = int(parts[idx].strip())
                        if s >= 1000:
                            result_seeds.add(s)
                            result_evidence.setdefault(s, []).append((rel_p, f'csv seed column: {s}'))

print(f"Total seeds found in result artifacts: {len(result_seeds)}")

all_known_used_seeds = executed_seed_sets | result_seeds
print(f"Total unique known used/evaluated seeds: {len(all_known_used_seeds)}")

# 3. Check specific candidate blocks
print("\n" + "="*80)
print("AUDIT OF SPECIFIC CANDIDATE BLOCKS")
print("="*80)

def audit_block(start, end, label):
    bset = set(range(start, end))
    used_in_scripts = bset & executed_seed_sets
    used_in_results = bset & result_seeds
    
    # Overlapping ranges
    overlapping_r = []
    for s_r, e_r, fn in executed_ranges:
        if max(s_r, start) < min(e_r, end):
            overlapping_r.append((s_r, e_r, fn))
            
    print(f"\nBlock: {label} ({start}-{end-1})")
    print(f"  Total seeds in block: {len(bset)}")
    print(f"  Seeds in execution scripts: {len(used_in_scripts)}")
    print(f"  Seeds in result files: {len(used_in_results)}")
    print(f"  Overlapping ranges: {len(overlapping_r)}")
    
    if used_in_scripts:
        sample = list(used_in_scripts)[:3]
        print(f"  Sample script hits: {sample}")
        for s in sample:
            print(f"    Seed {s}: {script_evidence[s][:2]}")
    if used_in_results:
        sample = list(used_in_results)[:3]
        print(f"  Sample result hits: {sample}")
        for s in sample:
            print(f"    Seed {s}: {result_evidence[s][:2]}")
    if overlapping_r:
        print(f"  Range overlaps: {overlapping_r[:3]}")
        
    status = "CONTAMINATED" if (used_in_scripts or used_in_results or overlapping_r) else "VIRGIN"
    print(f"  FINAL BLOCK STATUS: {status}")
    return status

audit_block(60000, 60050, "Candidate 1: 60000-60049")
audit_block(70000, 70050, "Candidate 2: 70000-70049")
audit_block(80000, 80050, "Candidate 3: 80000-80049")

# 4. Search for VIRGIN 50-seed blocks in various candidate spaces
print("\n" + "="*80)
print("SEARCHING FOR VIRGIN 50-SEED BLOCKS")
print("="*80)

tested_candidates = [
    (65000, 65050), (75000, 75050), (85000, 85050), (95000, 95050),
    (100000, 100050), (105000, 105050), (110000, 110050), (120000, 120050),
    (130000, 130050), (140000, 140050), (150000, 150050), (160000, 160050),
    (170000, 170050), (180000, 180050), (190000, 190050), (195000, 195050),
    (200000, 200050), (205000, 205050), (210000, 210050), (220000, 220050),
    (230000, 230050), (240000, 240050), (245000, 245050), (250000, 250050),
]

virgin_blocks = []
for s, e in tested_candidates:
    bset = set(range(s, e))
    if not (bset & all_known_used_seeds):
        # Also ensure no range overlaps
        overlaps = [r for r in executed_ranges if max(r[0], s) < min(r[1], e)]
        if not overlaps:
            virgin_blocks.append((s, e, f"{s}-{e-1}"))

print(f"Found {len(virgin_blocks)} candidate blocks with 0 execution & 0 result exposure:")
for s, e, lbl in virgin_blocks:
    print(f"  - {lbl}")

