#!/usr/bin/env python3
"""Inspect and map all shop routes in thomastschinkel_2945."""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

p = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

# Let's extract the route tables
import re
def extract_dict(var_name, text):
    m = re.search(rf"{var_name}\s*=\s*(\{{.*?\}})", text, re.DOTALL)
    if m:
        try:
            return eval(m.group(1))
        except Exception as e:
            return f"Error eval: {e}"
    return "Not found"

r110 = extract_dict("_R110_OLD_SHOPS", text)
v92 = extract_dict("_V92_TABLE", text)
v93 = extract_dict("_V93_ROUTE_BY_RIVAL", text)

print("=== _R110_OLD_SHOPS (Yarn Worlds) ===")
if isinstance(r110, dict):
    print(f"Total entries: {len(r110)}")
    for k, v in sorted(r110.items())[:15]:
        print(f"  {k} -> Route {v}")

print("\n=== _V92_TABLE (Overrides) ===")
if isinstance(v92, dict):
    print(f"Total entries: {len(v92)}")
    for k, v in sorted(v92.items())[:15]:
        print(f"  {k} -> Route {v}")

print("\n=== _V93_ROUTE_BY_RIVAL (Rival Signatures) ===")
if isinstance(v93, dict):
    print(f"Total entries: {len(v93)}")
    for k, v in sorted(v93.items())[:15]:
        print(f"  {k} -> Route {v}")

# Now let's check _R108_DATA (Non-Yarn Worlds)
pos = text.find("_R108_DATA")
if pos != -1:
    sub = text[pos:pos+1500]
    print("\n=== _R108_DATA definition snippet ===")
    print(sub[:500])
