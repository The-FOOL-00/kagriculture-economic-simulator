import sys, os
sys.path.insert(0, os.path.abspath('.'))
import candidates.slot2_aethel_refined_v2 as v2
import json

trace = v2._TRACE
print(f"Total turns in trace: {len(trace)}")
step0 = trace[0]
print("Step 0 action:", json.dumps(step0))

# Analyze worker counts over time
worker_counts = []
for s, act in enumerate(trace):
    f = 1 if act.get("farmer") else 0
    h = len(act.get("hands", []) or [])
    worker_counts.append(f + h)

print(f"Worker count at start: {worker_counts[0]}, at end: {worker_counts[-1]}, max: {max(worker_counts)}")

# Sample steps
for s in [0, 24, 48, 72, 96, 120, 240, 480, 700]:
    if s < len(trace):
        print(f"\nStep {s}:")
        print("  farmer:", trace[s].get("farmer"))
        print("  hands:", trace[s].get("hands")[:3], f"... ({len(trace[s].get('hands', []))} hands)")
        print("  market:", trace[s].get("market"))
