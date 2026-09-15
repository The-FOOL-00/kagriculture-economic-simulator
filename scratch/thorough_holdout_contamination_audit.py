import os
import re

TARGET_SEEDS = set(range(35000, 35200))
REPO_DIR = os.path.abspath(".")

# Whitelist our holdout script and results that we ran earlier
EXCLUDED_PATHS = {
    os.path.abspath("scratch/run_fresh_holdout_200seeds.py"),
    os.path.abspath("scratch/fresh_holdout_200seeds_results.json"),
    os.path.abspath("reports/WORKER_LABOR_BANDWIDTH_AND_HARVEST_RESERVATION_AUDIT_REPORT.md"),
    os.path.abspath("scratch/verify_contamination.py")
}

matches = []

seed_pattern = re.compile(r'\b(35[01][0-9]{2})\b')

for root, dirs, files in os.walk(REPO_DIR):
    # Ignore git and pycache
    if ".git" in root or "__pycache__" in root or ".gemini" in root:
        continue
    for f in files:
        f_path = os.path.abspath(os.path.join(root, f))
        if f_path in EXCLUDED_PATHS:
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext in [".py", ".md", ".json", ".txt", ".log", ".csv"]:
            try:
                with open(f_path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    found = seed_pattern.findall(content)
                    if found:
                        matches.append((f_path, set(found)))
            except Exception as e:
                pass

print("="*90)
print("THOROUGH CONTAMINATION AUDIT FOR SEEDS 35000-35199")
print("="*90)
print(f"Total historical matches found outside current audit files: {len(matches)}")
for p, s_set in matches:
    print(f"  File: {p} -> Seeds: {s_set}")

if len(matches) == 0:
    print("\nVERIFICATION RESULT: 100% PRISTINE! Zero historical contamination found.")
else:
    print("\nWARNING: Matches found!")
