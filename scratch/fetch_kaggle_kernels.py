import sys
import os
import json
from kaggle.api.kaggle_api_extended import KaggleApi

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

print("=== SEARCHING KAGGRICULTURE KERNELS ===")
kernels = api.kernels_list(search="kaggriculture", page_size=100)
print(f"Found {len(kernels)} kernels.")

k_list = []
for k in kernels:
    ref = str(getattr(k, 'ref', ''))
    title = str(getattr(k, 'title', ''))
    votes = getattr(k, 'totalVotes', getattr(k, 'total_votes', 0))
    author = str(getattr(k, 'author', ''))
    last_run = str(getattr(k, 'lastRunTime', getattr(k, 'last_run_time', '')))
    k_list.append({
        "ref": ref,
        "title": title,
        "votes": votes,
        "author": author,
        "last_run": last_run
    })
    print(f"[{ref}] (Votes: {votes}) Title: {title} | Run: {last_run}")

with open("scratch/kernels_list.json", "w", encoding="utf-8") as f:
    json.dump(k_list, f, indent=2)
