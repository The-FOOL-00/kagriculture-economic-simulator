import os
import glob
import re

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"
qual_seeds = set(range(50050, 50100))

# Search for any simulation of Dev002 or hedged portfolio on qualification seeds
hits = []
for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "external_repos" in root:
        continue
    for f in files:
        if f.endswith((".py", ".json", ".csv", ".txt", ".md")):
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                    txt = file.read()
                # If file mentions Dev002 or dev_002 or hedged_portfolio or Bedrock Strawberry
                if any(k in txt for k in ["Dev002", "dev_002", "dev002", "hedged_portfolio"]):
                    for s in qual_seeds:
                        # Check if s appears in a context of simulation or execution
                        matches = [m.start() for m in re.finditer(r"\b" + str(s) + r"\b", txt)]
                        if matches:
                            for idx in matches:
                                snippet = txt[max(0, idx-80):min(len(txt), idx+80)].replace("\n", " ")
                                hits.append((os.path.relpath(fp, BASE_DIR), s, snippet))
            except Exception:
                pass

print(f"Total hits with dev_002 / Dev002 / hedged_portfolio and seed in 50050-50099: {len(hits)}")
for path, seed, snip in hits:
    print(f"\nFile: {path} | Seed: {seed}")
    print(f"  Snippet: {snip}")
