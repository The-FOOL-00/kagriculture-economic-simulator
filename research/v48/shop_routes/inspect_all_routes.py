#!/usr/bin/env python3
"""Inspect all route tapes in thomastschinkel_2945."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v47.elite_corpus.agents.thomastschinkel_2945.main import _ROUTES

print("=== ALL ROUTES IN 2945 ===")
print("Total routes:", len(_ROUTES))
for k in sorted(_ROUTES.keys()):
    tape = _ROUTES[k]
    # inspect length, first action, sample market orders
    buys = []
    for step in range(len(tape)):
        act = tape[step]
        if isinstance(act, dict):
            for o in (act.get("market") or []):
                if o and len(o) >= 2 and o[0] in ("BUY_ANIMAL", "BUY_LAND"):
                    buys.append((step, o))
    print(f"Route {k:3d}: {len(tape)} steps | Capital Buys: {len(buys)} | Sample buys: {buys[:3]}")
