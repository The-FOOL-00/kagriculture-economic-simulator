import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    steps = json.load(f)["steps"]

def print_grid(step_num, p=1):
    obs = steps[step_num][p]["observation"]
    farm = obs["farms"][p]
    tiles = farm["tiles"]
    print(f"=== PLAYER {p} GRID AT STEP {step_num} (Day {step_num//24}) ===")
    for y, row in enumerate(tiles):
        row_str = []
        for x, t in enumerate(row):
            if t == "LOCKED":
                row_str.append(" . ")
            elif t is None:
                row_str.append("___")
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PASTURE":
                    a = t.get("animal")
                    a_code = a[0] if a else "E"
                    row_str.append(f"P_{a_code}")
                elif k == "PLANT":
                    c = t.get("crop")
                    w = t.get("water_level", 0)
                    row_str.append(f"{c[0]}_{w}")
                elif k == "SHED":
                    row_str.append("SHD")
                else:
                    row_str.append(k[:3])
            else:
                row_str.append(str(t)[:3])
        print(f"{y:2d}: " + " ".join(row_str))

print_grid(24, p=1)
print_grid(24, p=0)
print_grid(168, p=1)
print_grid(168, p=0)
