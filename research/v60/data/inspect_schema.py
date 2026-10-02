#!/usr/bin/env python3
"""V60 — Fixed replay parser. Inspects actual step schema first, then extracts teams."""
import json
from pathlib import Path

KEEP_DIR = Path("live_data/episodes_v31r2/keep")

# Read one a7 file to understand schema
a7_files = sorted(KEEP_DIR.glob("a7-*.json"))
print(f"a7 files: {len(a7_files)}")

with open(a7_files[0], 'r') as f:
    rep = json.load(f)

print("Top-level keys:", list(rep.keys()))
print("info:", rep.get('info'))
print("rewards:", rep.get('rewards'))
print("statuses:", rep.get('statuses'))
print("module_version:", rep.get('module_version'))
print("n_steps:", len(rep.get('steps', [])))

# Look at first step structure
steps = rep.get('steps', [])
if steps:
    s0 = steps[0]
    print("\nStep 0 type:", type(s0))
    if isinstance(s0, list):
        print("Step 0 len:", len(s0))
        for i, agent_step in enumerate(s0):
            print(f"  agent {i} type:", type(agent_step))
            if isinstance(agent_step, dict):
                print(f"  agent {i} keys:", list(agent_step.keys()))
                obs = agent_step.get('observation', {})
                if obs:
                    print(f"  obs keys:", list(obs.keys())[:10])
                action = agent_step.get('action', None)
                print(f"  action:", str(action)[:100])
            elif isinstance(agent_step, int):
                print(f"  agent {i} value:", agent_step)
    elif isinstance(s0, dict):
        print("Step 0 keys:", list(s0.keys()))
