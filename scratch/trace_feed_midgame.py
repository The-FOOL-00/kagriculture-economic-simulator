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

for step in range(720):
    if env.done:
        break
    obs = env.state[0].observation
    day = obs['day']
    hr = obs['hour']
    
    action = hybrid.agent(obs)
    env.step([action, {'farmer': ['PASS'], 'hands': [], 'market': []}])
    
    f = env.state[0].observation['farms'][0]
    p = env.state[0].observation['private']
    
    if 13 <= day <= 16:
        # Check pasture feed status
        unfed_cows = 0
        unfed_sheep = 0
        total_cows = 0
        total_sheep = 0
        for row in f['tiles']:
            for cell in row:
                if isinstance(cell, dict) and cell.get('kind') == 'PASTURE':
                    if cell.get('animal') == 'COW':
                        total_cows += 1
                        if not cell.get('fed_today', False): unfed_cows += 1
                    elif cell.get('animal') == 'SHEEP':
                        total_sheep += 1
                        if not cell.get('fed_today', False): unfed_sheep += 1
                        
        if hr == 23 or hr == 0:
            print(f"Step {step:3d} (Day {day:2d}, Hr {hr:2d}) | Money: ${f['money']:6.0f} | Cows: {total_cows} (Unfed: {unfed_cows}) | Sheep: {total_sheep} (Unfed: {unfed_sheep}) | Shed Wheat: {p['shed'].get('WHEAT', 0)} | Worker Wheat: {[inv.get('WHEAT', 0) for inv in p.get('inventories', [])]}")
