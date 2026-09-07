import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from collections import defaultdict

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

# For each tile (x, y), what was planted on what day?
planted_timeline = defaultdict(list)
for step_idx in range(720):
    farm = env.steps[step_idx][0]['observation']['farms'][0]
    day = step_idx // 24
    hour = step_idx % 24
    for y, row in enumerate(farm['tiles']):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                crop = t.get('crop')
                planted_day = t.get('planted_day')
                if (crop, planted_day) not in planted_timeline[(x, y)]:
                    planted_timeline[(x, y)].append((crop, planted_day))

print("=== V2 Crop Tile Map by Quadrant ===")
quad_crops = defaultdict(lambda: defaultdict(list))
for (x, y), crops in sorted(planted_timeline.items()):
    q = "NW" if x < 5 and y < 5 else ("NE" if x >= 5 and y < 5 else ("SW" if x < 5 and y >= 5 else "SE"))
    crop_names = [c[0] for c in crops]
    quad_crops[q][tuple(crop_names)].append((x, y))

for q, d in sorted(quad_crops.items()):
    print(f"\nQuadrant {q}:")
    for crops, tiles in sorted(d.items()):
        print(f"  {crops}: {len(tiles)} tiles -> {tiles[:6]}")
