import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from scratch.test_hybrid_features import HybridCandidate

h = HybridCandidate()
env = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 100})
starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
env.run([lambda o, c=None: h(o, c), starter])

for s in [23, 119, 239, 263, 359, 479, 599, 711, 719]:
    obs = env.steps[s][0]['observation']
    f = obs['farms'][0]
    p = obs['private']
    day = s // 24
    hour = s % 24
    m = f['money']
    h_cnt = len(f.get('hands', []))
    cows = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'COW')
    sheep = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    pastures = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'PASTURE')
    crops = {}
    weeds = 0
    for r in f['tiles']:
        for t in r:
            if isinstance(t, dict):
                if t.get('kind') == 'PLANT':
                    crops[t.get('crop')] = crops.get(t.get('crop'), 0) + 1
                elif t.get('kind') == 'WEED':
                    weeds += 1
    print(f"Step {s:3d} (D{day:02d}:H{hour:02d}): Cash=${m:,.1f} | Hands={h_cnt} | Cows={cows}, Sheep={sheep}, Past={pastures} | Crops={crops} | Weeds={weeds}")
    print(f"   Shed: {p.get('shed')}")
