# SPDX-License-Identifier: MIT
"""Kagriculture V35 Opening Action Trace & Action Map Inspector.

Inspects the exact A7 actions, unit tasks, and market transactions during
the opening day (steps 0 to 24).
"""

from __future__ import annotations
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent


def trace_opening_actions(seed: int = 249675, steps: int = 24):
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": steps + 2})
    env.reset()
    a7 = load_agent("E9_AST")

    trace = []
    while not env.done and len(trace) < steps:
        obs = env.steps[-1][0]["observation"]
        step = int(obs.get("step", 0) or 0)
        farms = obs.get("farms", []) or []
        farm = farms[0] if farms else {}
        cash = float(farm.get("money", 0.0) or 0.0)
        shed = obs.get("private", {}).get("shed", {}) or {}
        seeds = obs.get("private", {}).get("seeds", {}) or {}
        market = obs.get("market", {}) or {}
        prices = market.get("prices", {}) or {}

        act = a7.act(obs)
        trace.append({
            "step": step,
            "cash": cash,
            "shed": {k: v for k, v in shed.items() if v > 0},
            "seeds": {k: v for k, v in seeds.items() if v > 0},
            "prices": prices,
            "action": act,
        })
        env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])

    out_file = os.path.join(REPO_ROOT, "candidates", "v35_a7_opening", "opening_tape_trace.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)
    print(f"Saved {out_file} ({len(trace)} steps)")
    for t in trace[:12]:
        mkt = t["action"].get("market", [])
        farmer = t["action"].get("farmer", [])
        hands = t["action"].get("hands", [])
        print(f"Step {t['step']:2d} | Cash: ${t['cash']:7.1f} | Farmer: {farmer} | Market: {mkt}")


if __name__ == "__main__":
    trace_opening_actions()
