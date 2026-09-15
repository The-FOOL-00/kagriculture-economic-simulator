import json
import zlib
import base64
from collections import Counter, defaultdict

with open("candidates/slot2_aethel_refined_v2.py", "r") as f:
    code = f.read()

# Extract the trace
start_marker = "b85decode(\n    '"
end_marker = "'\n)).decode("
start_idx = code.find(start_marker) + len(start_marker)
end_idx = code.find(end_marker, start_idx)
b85_str = code[start_idx:end_idx]

trace = json.loads(zlib.decompress(base64.b85decode(b85_str)).decode("utf-8"))

print(f"Total steps in V2 trace: {len(trace)}")

# Let's print days 0-1 in full detail
for day in range(2):
    print(f"================== DAY {day} ==================")
    for step in range(day * 24, (day + 1) * 24):
        act = trace[step]
        m = act.get("market", [])
        units = [("farmer", act.get("farmer"))] + [(f"hand_{i}", h) for i, h in enumerate(act.get("hands", []))]
        non_trivial = [(name, u) for name, u in units if u and u[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST")]
        if m or non_trivial:
            print(f"  Step {step} (Hour {step%24}):")
            if m:
                print(f"    Market: {m}")
            if non_trivial:
                print(f"    Actions: {non_trivial}")


