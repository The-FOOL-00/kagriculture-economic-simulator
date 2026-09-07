import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make('kaggriculture', configuration={'seed': 100})
env.reset()

for s in range(719):
    obs = env.state[0].observation
    act = v2.agent(obs)
    env.step([act, None])
    
    if s in (23, 119, 239, 263, 359, 479, 599, 711, 718):
        f = env.state[0].observation['farms'][0]
        p = env.state[0].observation['private']
        cows = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'COW')
        sheep = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'SHEEP')
        straw = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY')
        melons = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('crop') == 'MELON')
        wheat = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('crop') == 'WHEAT')
        pastures = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'PASTURE')
        print(f"V2 Step {s:3d} (D{s//24:2d} H{s%24:2d}): Cash=${f['money']:8.1f} | Quads={f['unlocked_quadrants']} | Hands={len(f['hands'])} | Pas={pastures} Cow={cows} Shp={sheep} | Mel={melons} Str={straw} Wht={wheat} | Shed={p['shed']}")

print("V2 Final Reward:", env.steps[-1][0]["reward"])
