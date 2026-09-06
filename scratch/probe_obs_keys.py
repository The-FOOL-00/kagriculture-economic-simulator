import json

with open("scratch/replays/Crop_Dusta_104824599.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps")
step1_obs = steps[1][1]["observation"]
print("Step 1 P1 obs keys:", list(step1_obs.keys()))
for k, v in step1_obs.items():
    if k in ['day', 'hour', 'step', 'player']:
        print(f"  {k}: {v}")
    elif k in ['private']:
        print(f"  {k}: {v}")
    elif k in ['farms']:
        print(f"  farms type: {type(v)}, len: {len(v)}")
        if isinstance(v, list) and len(v) > 0:
            print(f"  farms[1] keys: {list(v[1].keys()) if isinstance(v[1], dict) else type(v[1])}")
            for fk, fv in v[1].items():
                if fk in ['cash', 'quadrants', 'shed', 'cows', 'sheep', 'pastures', 'hands']:
                    print(f"    {fk}: {fv}")
