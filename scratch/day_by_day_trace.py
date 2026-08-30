import sys
import os
import importlib.util

sys.path.insert(0, os.path.abspath('.'))
spec = importlib.util.spec_from_file_location('hybrid', 'agents/hybrid_6c3s_10m.py')
hybrid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hybrid)

from kaggle_environments import make

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 10001})
env.reset()

print("=" * 115)
print(f"{'DAY':<4} | {'CASH':<8} | {'COWS':<5} | {'SHEEP':<6} | {'PAST':<5} | {'MELONS':<7} | {'CARROTS':<8} | {'WHEAT':<6} | {'MILK':<5} | {'WOOL':<5} | {'FERT':<5} | {'SALES':<20}")
print("=" * 115)

daily_sales = []

for step in range(720):
    obs = env.state[0].observation
    action = hybrid.agent(obs)
    
    for o in action.get('market', []):
        if o[0] == 'SELL':
            daily_sales.append(f"{o[1]}:{o[2]}")
            
    env.step([action, {'farmer': ['PASS'], 'hands': [], 'market': []}])
    
    day = obs['day']
    hr = obs['hour']
    
    if hr == 23:
        f = env.state[0].observation['farms'][0]
        p = env.state[0].observation['private']
        shed = p.get('shed', {})
        
        cows = 0
        sheep = 0
        pastures = 0
        melons = 0
        carrots = 0
        wheat_p = 0
        for row in f['tiles']:
            for cell in row:
                if isinstance(cell, dict):
                    k = cell.get('kind')
                    if k == 'PASTURE':
                        pastures += 1
                        if cell.get('animal') == 'COW': cows += 1
                        elif cell.get('animal') == 'SHEEP': sheep += 1
                    elif k == 'PLANT':
                        c = cell.get('crop')
                        if c == 'MELON': melons += 1
                        elif c == 'CARROT': carrots += 1
                        elif c == 'WHEAT': wheat_p += 1
                        
        sales_str = ", ".join(daily_sales[-5:]) if daily_sales else "None"
        daily_sales = []
        print(f"{day:<4d} | ${f['money']:<7.0f} | {cows:<5d} | {sheep:<6d} | {pastures:<5d} | {melons:<7d} | {carrots:<8d} | {wheat_p:<6d} | {shed.get('MILK',0):<5d} | {shed.get('WOOL',0):<5d} | {shed.get('FERTILIZER',0):<5d} | {sales_str:<20}")

print("=" * 115)
print(f"Final Terminal Cash: ${env.steps[-1][0].reward:,.2f}")
print("=" * 115)
