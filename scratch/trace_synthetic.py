import sys
import os
import importlib.util

sys.path.insert(0, os.path.abspath('.'))
spec = importlib.util.spec_from_file_location('synth', 'agents/synthetic_suite.py')
synth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synth)

from kaggle_environments import make

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 10001})
env.reset()
for step in range(120):
    obs = env.state[0].observation
    action = synth.balanced_agent(obs)
    env.step([action, {'farmer': ['PASS'], 'hands': [], 'market': []}])
    f = env.state[0].observation['farms'][0]
    p = env.state[0].observation['private']
    day = obs['day']
    hr = obs['hour']
    if step % 24 == 0 or step < 10:
        print(f"Step {step:3d} (Day {day:2d}, Hr {hr:2d}) | Money: ${f['money']:6.0f} | Actions: {action['farmer']} Hands: {len(action['hands'])} Market: {action['market']}")
