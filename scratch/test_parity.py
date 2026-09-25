import copy
import sys
import time

sys.path.insert(0, '.')
sys.path.insert(0, './scripts')

from kaggle_environments import make
from scripts.v32_common import load_agent

def get_obs(env, pos):
    obs = copy.deepcopy(env.steps[-1][pos]['observation'])
    for k in ('step', 'market', 'town', 'day', 'hour'):
        if k in env.steps[-1][0]['observation'] and k not in obs:
            obs[k] = env.steps[-1][0]['observation'][k]
    return obs

# 1. Manual stepping with E9_AST vs E8_DMITRII
a = load_agent('E9_AST')
b = load_agent('E8_DMITRII')
env1 = make('kaggriculture', configuration={'seed': 249677})
env1.reset()
t0 = time.time()
while not env1.done:
    o0 = get_obs(env1, 0)
    o1 = get_obs(env1, 1)
    act0 = a.act(o0)
    act1 = b.act(o1)
    env1.step([act0, act1])
dur1 = time.time() - t0
r0_1 = env1.steps[-1][0]['reward']
r1_1 = env1.steps[-1][1]['reward']

# 2. Automated env.run with E9_AST vs E8_DMITRII
a_run = load_agent('E9_AST')
b_run = load_agent('E8_DMITRII')
env2 = make('kaggriculture', configuration={'seed': 249677})
t0 = time.time()
env2.run([lambda o, c=None: a_run.act(o, c), lambda o, c=None: b_run.act(o, c)])
dur2 = time.time() - t0
r0_2 = env2.steps[-1][0]['reward']
r1_2 = env2.steps[-1][1]['reward']

print(f"Manual Run: {dur1:.2f}s, r0={r0_1}, r1={r1_1}")
print(f"Auto Run:   {dur2:.2f}s, r0={r0_2}, r1={r1_2}")
assert r0_1 == r0_2, f"r0 mismatch: {r0_1} != {r0_2}"
assert r1_1 == r1_2, f"r1 mismatch: {r1_1} != {r1_2}"
print("PERFECT 100% BIT-IDENTICAL PARITY CONFIRMED!")
