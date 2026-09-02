import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

nb_path = "scratch/kernels/kaitofukami__238-238-known-streams-v58-minimax-closed-loop/238-238-known-streams-v58-minimax-closed-loop.ipynb"

with open(nb_path, "r", encoding="utf-8", errors="ignore") as f:
    nb = json.load(f)

print(f"Total cells in Kaitofukami notebook: {len(nb.get('cells', []))}")

for i, cell in enumerate(nb.get("cells", [])):
    ctype = cell.get("cell_type")
    source = "".join(cell.get("source", []))
    if ctype == "code":
        print(f"\n==========================================")
        print(f"CODE CELL {i} ({len(source)} chars)")
        print(f"==========================================")
        # print first 1000 chars
        print(source[:1200])
        if len(source) > 1200:
            print("...")
            print(source[-500:])
