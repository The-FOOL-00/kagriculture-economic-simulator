import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/crop_dusta_104824599_full_log.json', 'r') as f:
    full_data = json.load(f)

log = full_data['log']

print(f"=== DETAILED STEPS 0 TO 210 OF CROP DUSTA ===")

for row in log[:210]:
    s = row['step']
    evs = row['events']
    m = row['money']
    w = row['workers']
    p = row['pastures']
    c = row['cows']
    sh = row['sheep']
    quads = row['quads']
    crops = row['crops']
    shed = row['shed']
    cum_w = row['cum_wheat']
    
    ev_str = " | ".join(evs) if evs else ""
    crops_str = " ".join([f"{k}:{v}" for k, v in crops.items()]) if crops else "none"
    shed_str = " ".join([f"{k}:{v}" for k, v in shed.items()]) if shed else "empty"
    print(f"[{s:03d}] ${m:7.1f} | W:{w:2d} | P:{p:2d} | C:{c:2d} S:{sh:2d} | Q:{quads} | Crops:[{crops_str}] | Shed:[{shed_str}] | W_in:{cum_w:3d} | {ev_str}")
