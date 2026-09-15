import os
import re

TARGET_RANGE = range(85000, 85500)
REPO_DIR = os.path.abspath(".")

seed_pattern = re.compile(r'\b(85[0-4][0-9]{2})\b')
matches = []

for root, dirs, files in os.walk(REPO_DIR):
    if ".git" in root or "__pycache__" in root or ".gemini" in root:
        continue
    for f in files:
        f_path = os.path.abspath(os.path.join(root, f))
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
print("ZERO-CONTAMINATION AUDIT FOR SEED BLOCK 85000-85499 (N=500)")
print("="*90)
print(f"Total occurrences found across all repo files: {len(matches)}")
for p, s_set in matches:
    print(f"  Match in: {p} -> {s_set}")

if len(matches) == 0:
    print("\nVERIFICATION SUCCESS: 0 CONTAMINATIONS FOUND! Range 85000-85499 is 100% PRISTINE.")
else:
    print("\nWARNING: CONTAMINATION DETECTED!")
