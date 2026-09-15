import json

with open('scratch/audit2_1_seed50081_timeline.json', 'r') as f:
    data = json.load(f)

for row in data['timeline']:
    if row['step'] in [163, 164, 165, 216, 217, 218, 258, 259, 260, 695, 696]:
        print(f"=== STEP {row['step']} ===")
        print(f"  Cash: V2={row['cash_v2']}, Dmi={row['cash_dmi']}")
        print(f"  V2 Market: {row['act_v2_market']}")
        print(f"  Dmi Market: {row['act_dmi_market']}")
        print(f"  Tile Diffs: {row['tile_diffs']}")
        print(f"  V2 Hands: {row['act_v2_hands']}")
        print(f"  Dmi Hands: {row['act_dmi_hands']}")
