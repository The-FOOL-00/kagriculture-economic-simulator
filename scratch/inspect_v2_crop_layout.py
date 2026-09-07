import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

# Track what crops were planted where
tile_crops = {}
for step_idx in range(720):
    farm = env.steps[step_idx][0]['observation']['farms'][0]
    for y, row in enumerate(farm['tiles']):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                c = t.get('crop')
                if (x, y) not in tile_crops:
                    tile_crops[(x, y)] = set()
                tile_crops[(x, y)].add(c)

print("Total tiles used for crops in V2:", len(tile_crops))
strawberry_tiles = [pos for pos, crops in tile_crops.items() if 'STRAWBERRY' in crops]
print(f"Total tiles that grew STRAWBERRY in V2 ({len(strawberry_tiles)}):")
print(sorted(strawberry_tiles))
melon_tiles = [pos for pos, crops in tile_crops.items() if 'MELON' in crops]
print(f"Total tiles that grew MELON in V2 ({len(melon_tiles)}):")
print(sorted(melon_tiles))
