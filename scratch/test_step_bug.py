import sys
from kaggle_environments import make

p0_obs_steps = []
p1_obs_steps = []

def agent0(obs, cfg):
    p0_obs_steps.append({
        'step_in_obs': 'step' in obs,
        'step_val': obs.get('step'),
        'day': obs.get('day'),
        'hour': obs.get('hour'),
        'keys': sorted(list(obs.keys()))
    })
    return []

def agent1(obs, cfg):
    p1_obs_steps.append({
        'step_in_obs': 'step' in obs,
        'step_val': obs.get('step'),
        'day': obs.get('day'),
        'hour': obs.get('hour'),
        'keys': sorted(list(obs.keys()))
    })
    return []

env = make('kaggriculture', configuration={'episodeSteps': 20, 'seed': 42}, debug=True)
env.run([agent0, agent1])

print('=== P0 OBS SUMMARY (first 5 turns) ===')
for i, d in enumerate(p0_obs_steps[:5]):
    print(f"Turn {i}: in_obs={d['step_in_obs']}, step={d['step_val']}, day={d['day']}, hour={d['hour']}")

print('\n=== P1 OBS SUMMARY (first 5 turns) ===')
for i, d in enumerate(p1_obs_steps[:5]):
    print(f"Turn {i}: in_obs={d['step_in_obs']}, step={d['step_val']}, day={d['day']}, hour={d['hour']}")

print('\n=== KEYS COMPARISON ===')
print('P0 keys:', p0_obs_steps[0]['keys'])
print('P1 keys:', p1_obs_steps[0]['keys'])
diff01 = set(p0_obs_steps[0]['keys']) - set(p1_obs_steps[0]['keys'])
diff10 = set(p1_obs_steps[0]['keys']) - set(p0_obs_steps[0]['keys'])
print('P0 keys - P1 keys:', diff01)
print('P1 keys - P0 keys:', diff10)

print('\n=== ALL TURNS STEP CHECK ===')
p0_missing_step = [i for i, d in enumerate(p0_obs_steps) if not d['step_in_obs'] or d['step_val'] is None]
p1_missing_step = [i for i, d in enumerate(p1_obs_steps) if not d['step_in_obs'] or d['step_val'] is None]
print(f'P0 turns with missing/None step: {len(p0_missing_step)} / {len(p0_obs_steps)}')
print(f'P1 turns with missing/None step: {len(p1_missing_step)} / {len(p1_obs_steps)}')

print('\n=== STEP COMPARISON PER TURN ===')
for i in range(len(p0_obs_steps)):
    s0 = p0_obs_steps[i]['step_val']
    s1 = p1_obs_steps[i]['step_val']
    d0 = p0_obs_steps[i]['day']
    h0 = p0_obs_steps[i]['hour']
    print(f"Index {i:2d} | P0 step={s0}, day={d0}, hour={h0} | P1 in_obs={p1_obs_steps[i]['step_in_obs']}, step={s1}")
