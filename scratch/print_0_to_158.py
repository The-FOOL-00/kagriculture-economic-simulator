import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/crop_dusta_104824599_full_log.json', 'r') as f:
    full_data = json.load(f)

log = full_data['log']

print("=== CROP DUSTA STEPS 0 TO 158 ===")
for r in log[:159]:
    s = r['step']
    evs = r['events']
    if len(evs) > 0 or s % 10 == 0:
        ev_str = " | ".join(evs) if evs else ""
        crops_str = " ".join([f"{k}:{v}" for k, v in r['crops'].items()]) if r['crops'] else "none"
        shed_str = " ".join([f"{k}:{v}" for k, v in r['shed'].items()]) if r['shed'] else "empty"
        print(f"[{s:03d}] ${r['money']:7.1f} | W:{r['workers']:2d} | P:{r['pastures']:2d} | C:{r['cows']:2d} S:{r['sheep']:2d} | Q:{r['quads']} | Crops:[{crops_str}] | Shed:[{shed_str}] | Win:{r['cum_wheat']:3d} | {ev_str}")
