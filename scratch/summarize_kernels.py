import os
import sys
import glob

def summarize_kernels():
    kernel_dirs = glob.glob("scratch/kernels/*")
    print(f"Downloaded {len(kernel_dirs)} kernels:")
    
    for kdir in sorted(kernel_dirs):
        kname = os.path.basename(kdir)
        files = os.listdir(kdir)
        print(f"\n==========================================")
        print(f"KERNEL: {kname}")
        print(f"Files: {files}")
        
        # Read .ipynb or .py or .md
        for f in files:
            fpath = os.path.join(kdir, f)
            if f.endswith('.py'):
                print(f"\n--- Python File: {f} ({os.path.getsize(fpath)} bytes) ---")
                with open(fpath, "r", encoding="utf-8", errors="ignore") as pyf:
                    lines = pyf.readlines()
                    print("First 35 lines:")
                    print("".join(lines[:35]))
                    print("...")
            elif f.endswith('.ipynb'):
                import json
                print(f"\n--- Notebook: {f} ({os.path.getsize(fpath)} bytes) ---")
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as nbf:
                        nb = json.load(nbf)
                    cells = nb.get("cells", [])
                    print(f"Total cells: {len(cells)}")
                    # Print markdown summaries and key code definitions
                    for c_idx, c in enumerate(cells):
                        ctype = c.get("cell_type")
                        source = "".join(c.get("source", []))
                        if ctype == "markdown" and any(w in source.lower() for w in ["meta", "strategy", "win", "elo", "top", "route", "livestock", "melon", "summary", "conclusion", "table"]):
                            print(f"\n[Markdown Cell {c_idx}]:\n{source[:400]}\n...")
                        elif ctype == "code" and any(w in source.lower() for w in ["def agent", "class", "strategy", "meta", "routes", "simulate"]):
                            print(f"\n[Code Cell {c_idx} snippet]:\n{source[:300]}\n...")
                except Exception as e:
                    print(f"Error parsing notebook: {e}")

if __name__ == "__main__":
    summarize_kernels()
