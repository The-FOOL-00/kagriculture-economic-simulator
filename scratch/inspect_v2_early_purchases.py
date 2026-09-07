import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

# Inspect market orders and actions on Days 0 to 12
for step_idx in range(0, 12 * 24):
    day = step_idx // 24
    hour = step_idx % 24
    step = env.steps[step_idx]
    act = step[0].get('action', {})
    m_orders = act.get('market', []) or act.get('market_orders', [])
    
    # Filter for seed buys or unlocks
    buys = [o for o in m_orders if o[0] in ('BUY_SEED', 'BUY_ANIMAL', 'BUY', 'UNLOCK')]
    if buys or hour == 0:
        money = env.steps[step_idx][0]['observation']['farms'][0]['money']
        if buys:
            print(f"D{day:2d} H{hour:2d} (Step {step_idx:3d}): Money=${money:,.0f} | Buys={buys}")
