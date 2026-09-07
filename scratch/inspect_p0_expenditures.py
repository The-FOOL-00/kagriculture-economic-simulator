import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([prime_agent, v2_agent])

expenditures = {}
total_spent = 0

for step_idx, step in enumerate(env.steps):
    act = step[0].get('action', {})
    m_orders = act.get('market', []) or act.get('market_orders', [])
    for order in m_orders:
        cmd = order[0]
        if cmd == 'HIRE':
            expenditures['HIRE'] = expenditures.get('HIRE', 0) + 1
        elif cmd in ('BUY_SEED', 'BUY_PRODUCT', 'BUY_ANIMAL', 'BUY_LAND', 'UNLOCK'):
            key = f"{cmd}_{order[1]}" if len(order) > 1 else cmd
            qty = order[2] if len(order) > 2 else 1
            expenditures[key] = expenditures.get(key, 0) + qty

print("P0 Expenditures across all 720 steps:")
for k, v in sorted(expenditures.items()):
    print(f"  {k}: {v}")
