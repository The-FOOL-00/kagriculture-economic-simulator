import sys, os, time
sys.path.insert(0, '.')
sys.path.insert(0, './scripts')

from kaggle_environments import make
from scripts.v32_common import load_agent

a = load_agent('E2_A7')
b = load_agent('E0_V3')
env = make('kaggriculture', configuration={'seed': 249635})
env.reset()
t0 = time.time()
while not env.done:
    o0 = env.steps[-1][0]['observation']
    o1 = env.steps[-1][1]['observation']
    act0 = a.act(o0)
    act1 = b.act(o1)
    env.step([act0, act1])
dur = time.time() - t0
r0 = env.steps[-1][0]['reward']
r1 = env.steps[-1][1]['reward']
print(f"Manual step completed in {dur:.2f}s ({len(env.steps)/dur:.1f} SPS), r0={r0}, r1={r1}")
