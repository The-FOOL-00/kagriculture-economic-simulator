import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

# Find all pasture tiles at the end of the game
farm = env.steps[719][0]['observation']['farms'][0]
pastures = []
for y, row in enumerate(farm['tiles']):
    for x, t in enumerate(row):
        if isinstance(t, dict) and t.get('kind') == 'PASTURE':
            anim = t.get('animal')
            pastures.append(((x, y), anim))

print(f"Total pastures built by V2: {len(pastures)}")
print("V2 Pasture coordinates and animals:")
for pos, anim in sorted(pastures):
    print(f"  {pos}: {anim}")
