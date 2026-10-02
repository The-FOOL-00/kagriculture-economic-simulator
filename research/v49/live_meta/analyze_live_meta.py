#!/usr/bin/env python3
"""Analyze live meta scripts to identify new mechanisms and differences vs 2945/V48."""

import os
import re

META_DIR = os.path.dirname(os.path.abspath(__file__))

def analyze_file(filepath):
    print("=" * 80)
    print(f"ANALYZING: {os.path.basename(filepath)}")
    print("=" * 80)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Search for docstrings or header comments
    header_match = re.findall(r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')', content[:4000])
    if header_match:
        print("Header Docstring:")
        print(header_match[0][:1000])
        print("...")

    # Check for Chassis presence
    has_chassis = "class Chassis" in content or "def Chassis" in content
    print(f"Has Chassis (2945 descendant): {has_chassis}")

    # Check for key phrases / mechanisms
    keywords = [
        "herd_safe", "risk_aware", "sale_window", "race", "feed",
        "fertilizer", "carrot", "sovereign", "shepherd", "stack",
        "ORDERPRI", "order_priority", "route", "shed", "overrides",
        "market", "town"
    ]
    print("\nKeyword hits:")
    for kw in keywords:
        count = len(re.findall(re.escape(kw), content, re.IGNORECASE))
        if count > 0:
            print(f"  {kw}: {count} occurrences")

    # Look for diff comments or changelogs
    changelogs = re.findall(r'(?:change|update|v\d+|fix|patch|new|strategy|mod)[\w\s\:\-\.\,\(\)]*', content[:10000], re.IGNORECASE)
    print("\nInteresting lines/comments:")
    lines = content.split('\n')
    for i, line in enumerate(lines[:100]):
        if any(w in line.lower() for w in ["#", "v", "update", "patch", "strategy", "author", "score", "lb"]):
            if len(line.strip()) > 3 and not line.strip().startswith("# =="):
                print(f"  L{i+1}: {line.strip()[:100]}")

def main():
    for root, dirs, files in os.walk(META_DIR):
        for f in files:
            if f.endswith('_extracted.py') or f == 'kaggriculture-v15stack-submit.py':
                analyze_file(os.path.join(root, f))

if __name__ == '__main__':
    main()
