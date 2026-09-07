import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([prime_agent, v2_agent])

# Sum all sales by crop / item type for P0 and P1
p0_sales = {}
p1_sales = {}
p0_buys = {}
p1_buys = {}

for step_idx, step in enumerate(env.steps):
    for p_idx in [0, 1]:
        action = step[p_idx].get('action', {})
        if not action:
            continue
        m_orders = action.get('market', []) or action.get('market_orders', [])
        for order in m_orders:
            cmd = order[0]
            if cmd == 'SELL' and len(order) >= 3:
                item = order[1]
                qty = order[2]
                d = p0_sales if p_idx == 0 else p1_sales
                d[item] = d.get(item, 0) + qty
            elif cmd in ('BUY_SEED', 'BUY_ANIMAL', 'BUY') and len(order) >= 3:
                item = order[1]
                qty = order[2]
                d = p0_buys if p_idx == 0 else p1_buys
                d[item] = d.get(item, 0) + qty
            elif cmd == 'HIRE':
                d = p0_buys if p_idx == 0 else p1_buys
                d['HIRE'] = d.get('HIRE', 0) + 1


print("P0 Sales:", p0_sales)
print("P1 Sales:", p1_sales)
print("P0 Buys:", p0_buys)
print("P1 Buys:", p1_buys)
