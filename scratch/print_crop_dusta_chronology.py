import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/crop_dusta_104824599_full_log.json', 'r') as f:
    full_data = json.load(f)

log = full_data['log']

print(f"=== FULL STEP-BY-STEP CHRONOLOGY OF CROP DUSTA (0-720) ===")

for row in log:
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
    
    # Print if any event happened, or every 20 steps
    if len(evs) > 0 or s % 20 == 0 or s in [120, 121, 122, 123, 124, 198, 199, 200, 201, 202, 718, 719]:
        ev_str = " | ".join(evs) if evs else "idle/field-work"
        crops_str = " ".join([f"{k}:{v}" for k, v in crops.items()]) if crops else "none"
        shed_str = " ".join([f"{k}:{v}" for k, v in shed.items()]) if shed else "empty"
        print(f"[{s:03d}] Cash: ${m:7.1f} | W:{w:2d} | P:{p:2d} | C:{c:2d} S:{sh:2d} | Quads:{quads} | Crops:[{crops_str}] | Shed:[{shed_str}] | WheatBought:{cum_w} | {ev_str}")
