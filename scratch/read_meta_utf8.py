import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

files = [
    "scratch/kernel_summaries/kaitofukami__238-238-known-streams-v58-minimax-closed-loop.md",
    "scratch/kernel_summaries/busyaprime__what-actually-wins-on-the-kaggriculture-ladder.md",
    "scratch/kernel_summaries/georgymamarin__kaggriculture-daily-replays-the-live-meta-report.md",
    "scratch/kernel_summaries/boatlee__v21-r1-public-state-route-portfolio.md",
    "scratch/kernel_summaries/destbreso__a-dna-test-for-agents.md",
    "scratch/kernel_summaries/lynnsakurai__farming-score-v3-replay-revised.md"
]

for fpath in files:
    if os.path.exists(fpath):
        print(f"\n=======================================================")
        print(f"FILE: {fpath}")
        print(f"=======================================================")
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # print first 3500 chars
            print(content[:3500])
