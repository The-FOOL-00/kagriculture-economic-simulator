import os
import sys
import json
import glob

os.makedirs("scratch/kernel_summaries", exist_ok=True)
kernel_dirs = glob.glob("scratch/kernels/*")

for kdir in sorted(kernel_dirs):
    kname = os.path.basename(kdir)
    out_md = os.path.join("scratch/kernel_summaries", f"{kname}.md")
    
    with open(out_md, "w", encoding="utf-8") as out:
        out.write(f"# Kernel: {kname}\n\n")
        
        for fname in os.listdir(kdir):
            fpath = os.path.join(kdir, fname)
            if fname.endswith(".ipynb"):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as nbf:
                        nb = json.load(nbf)
                    cells = nb.get("cells", [])
                    out.write(f"## Notebook: {fname} ({len(cells)} cells)\n\n")
                    for i, c in enumerate(cells):
                        ctype = c.get("cell_type")
                        source = "".join(c.get("source", []))
                        if ctype == "markdown":
                            out.write(f"### [Markdown Cell {i}]\n{source}\n\n")
                        elif ctype == "code":
                            # Check if it defines agent or constants or key functions
                            if len(source) < 1500 or any(w in source for w in ["class ", "def agent", "def kaggle_agent", "def solve", "META", "ROUTES"]):
                                out.write(f"### [Code Cell {i}]\n```python\n{source[:2000]}\n```\n\n")
                except Exception as e:
                    out.write(f"Error reading {fname}: {e}\n")
            elif fname.endswith(".py"):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as pyf:
                        code = pyf.read()
                    out.write(f"## Python File: {fname}\n```python\n{code[:4000]}\n```\n\n")
                except Exception as e:
                    out.write(f"Error reading {fname}: {e}\n")

print(f"Generated summaries for {len(kernel_dirs)} kernels in scratch/kernel_summaries/")
