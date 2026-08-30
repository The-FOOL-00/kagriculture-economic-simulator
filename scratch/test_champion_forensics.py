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

print("=" * 80)
print("FORENSIC TRACE: FIRST 3 DAYS OF CORRECTED CHAMPION")
print("=" * 80)

for step in range(72):
    obs = env.state[0].observation
    action = hybrid.agent(obs)
    env.step([action, {'farmer': ['PASS'], 'hands': [], 'market': []}])
    f = env.state[0].observation['farms'][0]
    p = env.state[0].observation['private']
    day = obs['day']
    hr = obs['hour']
    
    # Count active cows/sheep on board
    cows = 0
    sheep = 0
    pastures = 0
    for row in f['tiles']:
        for cell in row:
            if isinstance(cell, dict) and cell.get('kind') == 'PASTURE':
                pastures += 1
                if cell.get('animal') == 'COW': cows += 1
                elif cell.get('animal') == 'SHEEP': sheep += 1
                
    if hr == 0 or step < 5:
        print(f"Step {step:2d} (Day {day:1d}, Hr {hr:2d}) | Money: ${f['money']:6.0f} | Cows: {cows} Sheep: {sheep} Pastures: {pastures} | Shed Wheat: {p['shed'].get('WHEAT', 0)} Cow: {p['shed'].get('COW', 0)} | Market: {action['market']}")

# Now finish 720 steps
while not env.done:
    obs = env.state[0].observation
    action = hybrid.agent(obs)
    env.step([action, {'farmer': ['PASS'], 'hands': [], 'market': []}])

final_r = env.steps[-1][0].reward
print("=" * 80)
print(f"FULL 720-STEP RESULT: Reward = ${final_r:,.2f} | Status = {env.state[0].status}")
print("=" * 80)
