import sys, os
sys.path.insert(0, os.path.abspath('.'))
import candidates.slot2_aethel_refined_v2 as v2

trace = v2._TRACE
for s in range(len(trace)):
    h = trace[s].get("hands")
    if h is not None and len(h) > 0:
        print(f"Step {s} has {len(h)} hands: {h[:2]}")
        if s > 30:
            break

print("\nSampling hands count across turns:")
for s in range(0, 720, 24):
    h_len = len(trace[s].get("hands", []) or [])
    print(f"Turn {s} (Day {s//24}): {h_len} hands")
