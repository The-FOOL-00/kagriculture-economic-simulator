"""Examine exact_raw_h2h_baseline - these have large margins vs old agent."""
import json

d = json.load(open('scratch/exact_raw_h2h_baseline.json'))
print('Keys in first item:', list(d[0].keys()))
print('Sample:', str(d[0])[:400])
print()
# These look like old agent vs Dmitrii - check the keys
for m in d[:3]:
    print('Match:', m)
