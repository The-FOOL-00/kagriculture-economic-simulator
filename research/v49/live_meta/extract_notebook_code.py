#!/usr/bin/env python3
"""Extract python code from downloaded ipynb notebooks."""

import os
import json
import glob

META_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_ipynb(ipynb_path, output_py_path):
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    code_cells = []
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            src = "".join(cell.get('source', []))
            code_cells.append(src)
    full_code = "\n\n# " + "="*70 + "\n# CELL\n# " + "="*70 + "\n\n".join(code_cells)
    with open(output_py_path, 'w', encoding='utf-8') as f:
        f.write(full_code)
    print(f"Extracted {len(code_cells)} cells to {output_py_path}")

def main():
    for root, dirs, files in os.walk(META_DIR):
        for f in files:
            if f.endswith('.ipynb'):
                in_path = os.path.join(root, f)
                out_path = os.path.join(root, f.replace('.ipynb', '_extracted.py'))
                try:
                    extract_ipynb(in_path, out_path)
                except Exception as e:
                    print(f"Error extracting {in_path}: {e}")

if __name__ == '__main__':
    main()
