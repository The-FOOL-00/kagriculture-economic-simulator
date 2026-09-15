from kaggle_environments import make
import sys, os, importlib.util

sys.path.insert(0, os.path.abspath('external_repos/kaggriculture-v66-agent'))
from main import agent as v66_agent

spec = importlib.util.spec_from_file_location('v2', 'agents/slot4_control_frozen_v2.py')
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42})
env.run([v66_agent, v2.agent])

steps = env.steps
print('Total steps:', len(steps))
for chk in [24, 72, 144, 216, 288, 360, 432, 504, 576, 648, 718]:
    obs0 = steps[chk][0]['observation']
    f0 = obs0['farms'][0]
    f1 = obs0['farms'][1]
    m0 = f0.get('money', 0)
    h0 = len(f0.get('hands', []))
    m1 = f1.get('money', 0)
    h1 = len(f1.get('hands', []))
    print(f"Step {chk:3d}: V66 money={m0:8.1f}, hands={h0:2d} | V2 money={m1:8.1f}, hands={h1:2d}")

f0_final = steps[718][0]['observation']['farms'][0]
print('\nV66 final tiles summary:')
tiles = f0_final.get('tiles', [])
crop_counts = {}
animal_counts = {}
for r in tiles:
    for c in r:
        if isinstance(c, dict):
            if c.get('kind') == 'PLANT':
                crop = c.get('crop')
                crop_counts[crop] = crop_counts.get(crop, 0) + 1
            elif c.get('animal'):
                a = c['animal']['kind']
                animal_counts[a] = animal_counts.get(a, 0) + 1
print('V66 Crops on ground at step 718:', crop_counts)
print('V66 Animals on ground at step 718:', animal_counts)

f1_final = steps[718][0]['observation']['farms'][1]
crop_counts1 = {}
animal_counts1 = {}
for r in f1_final.get('tiles', []):
    for c in r:
        if isinstance(c, dict):
            if c.get('kind') == 'PLANT':
                crop = c.get('crop')
                crop_counts1[crop] = crop_counts1.get(crop, 0) + 1
            elif c.get('animal'):
                a = c['animal']['kind']
                animal_counts1[a] = animal_counts1.get(a, 0) + 1
print('\nV2 Crops on ground at step 718:', crop_counts1)
print('V2 Animals on ground at step 718:', animal_counts1)
