import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

for name in ["kaitofukami__238-238-known-streams-v58-minimax-closed-loop.md", "busyaprime__what-actually-wins-on-the-kaggriculture-ladder.md"]:
    fpath = os.path.join("scratch/kernel_summaries", name)
    print(f"\n=======================================================")
    print(f"FULL TEXT: {name}")
    print(f"=======================================================")
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())
