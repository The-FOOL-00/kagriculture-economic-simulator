import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from scratch.test_hybrid_features import HybridCandidate
import candidates.slot2_aethel_refined_v2 as v2

h = HybridCandidate()
env = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 104817623})
env.run([lambda o, c=None: h(o, c), v2.agent])

for s in [23, 119, 239, 263, 359, 479, 599, 719]:
    obs0 = env.steps[s][0]['observation']
    obs1 = env.steps[s][1]['observation']
    f0 = obs0['farms'][0]
    f1 = obs1['farms'][1]
    p0 = obs0['private']
    p1 = obs1['private']
    mkt = obs0['market']
    print(f"Step {s:3d} (D{s//24:02d}:H{s%24:02d}): P0 Cash=${f0['money']:,.0f}, P1 Cash=${f1['money']:,.0f}")
    print(f"  P0 Shed: {p0.get('shed')}")
    print(f"  P1 Shed: {p1.get('shed')}")
    print(f"  Market Prices: Wheat={mkt['prices']['WHEAT']}, Mel={mkt['prices']['MELON']}, Milk={mkt['prices']['MILK']}")
