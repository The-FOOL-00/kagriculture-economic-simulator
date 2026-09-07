import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from scratch.test_grandmaster_sweep import GrandmasterCandidate

gm = GrandmasterCandidate()
env = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42})
starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
env.run([lambda o, c=None: gm(o, c), starter])

for s in [23, 119, 239, 263, 359, 479, 599, 711, 719]:
    obs = env.steps[s][0]['observation']
    f = obs['farms'][0]
    p = obs['private']
    day = s // 24
    hour = s % 24
    m = f['money']
    h = len(f.get('hands', []))
    print(f"Step {s:3d} (D{day:02d}:H{hour:02d}): Cash=${m:,.1f} | Hands={h} | Shed={p.get('shed')}")
    # Animals
    cows = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'COW')
    sheep = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    hungry = sum(1 for r in f['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'PASTURE' and t.get('animal') and not t.get('fed_today'))
    print(f"  Animals: Cows={cows}, Sheep={sheep}, Hungry={hungry}")
