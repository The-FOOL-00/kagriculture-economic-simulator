import time
import sys
import os

sys.path.insert(0, '.')
sys.path.insert(0, './scripts')

from scripts.v32_common import load_agent
from kaggle_environments import make

t0 = time.time()
env = make('kaggriculture', configuration={'seed': 249635})
a = load_agent('E2_A7')
b = load_agent('E0_V3')
env.run([lambda o, c=None: a.act(o, c), lambda o, c=None: b.act(o, c)])
dur = time.time() - t0
r0 = env.steps[-1][0]["reward"]
r1 = env.steps[-1][1]["reward"]
print(f"720 steps completed in {dur:.2f}s ({720/dur:.1f} SPS), r0={r0}, r1={r1}")
