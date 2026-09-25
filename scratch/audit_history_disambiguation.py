"""
Comprehensive History-Disambiguation Forensic Audit
Tests whether observation/action history disambiguates teacher actions across H0, H2, H4, H8, H16, H32.
"""
import sys, os, json, math
from collections import defaultdict, Counter
import numpy as np

# Load prefix dataset from P7
with open("results/v32_p7_prefixes.json") as f:
    prefixes = json.load(f)

print(f"Loaded {len(prefixes)} prefix demonstrations from results/v32_p7_prefixes.json")

# Structure of prefixes
sample_key = list(prefixes.keys())[0]
sample = prefixes[sample_key]
print(f"Sample key: {sample_key}")
print(f"Sample keys: {list(sample.keys())}")
print(f"Number of steps in sample: {len(sample.get('steps', []))}")

# Check action consistency across all demonstrations at each step 0..24
step_farmer_acts = defaultdict(list)
step_market_acts = defaultdict(list)
step_hand_acts = defaultdict(list)

for key, pdata in prefixes.items():
    teacher = pdata.get("teacher")
    steps = pdata.get("steps", [])
    for s in steps:
        step_idx = s.get("step")
        act = s.get("action", {})
        farmer = act.get("farmer")
        market = act.get("market")
        hands = act.get("hands")
        
        step_farmer_acts[step_idx].append((json.dumps(farmer), teacher))
        step_market_acts[step_idx].append((json.dumps(market), teacher))

print("\n--- Farmer Action Distribution across demonstrations at Steps 0..12 ---")
for t in range(13):
    acts = [a[0] for a in step_farmer_acts[t]]
    c = Counter(acts)
    entropy = -sum((cnt / len(acts)) * math.log2(cnt / len(acts)) for cnt in c.values()) if acts else 0
    print(f"Step {t:2d} (N={len(acts)}): Entropy={entropy:.4f} bits | Top actions: {dict(c.most_common(3))}")

# Now let's analyze Step 3 specifically:
print("\n--- Deep Dive on Step 3 across all demonstrations ---")
s3_acts = step_farmer_acts[3]
c3 = Counter(a[0] for a in s3_acts)
print(f"Step 3 unique farmer actions across {len(s3_acts)} demos: {dict(c3)}")
