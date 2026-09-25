# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from collections import defaultdict
from kaggle_environments import make
from scripts.v32_common import load_agent

a7 = load_agent('E9_AST')
dmitrii = load_agent('E8_DMITRII')
env = make('kaggriculture', configuration={'seed': 249677})
env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmitrii.act(o, c)])

# Cash balance decomposition
# Final cash = Initial cash + Total Sales Revenue - Total Purchase Expenses - Total Wages Paid - Land/Hire costs
rev_a7 = defaultdict(float)
rev_dm = defaultdict(float)
cost_a7 = defaultdict(float)
cost_dm = defaultdict(float)

# Compare cash delta step by step
diff_events = []

for s in range(len(env.steps) - 1):
    step_now = env.steps[s]
    step_next = env.steps[s+1]
    
    m0_now = step_now[0]['observation']['farms'][0]['money']
    m0_next = step_next[0]['observation']['farms'][0]['money']
    m1_now = step_now[1]['observation']['farms'][1]['money']
    m1_next = step_next[1]['observation']['farms'][1]['money']
    
    d0 = m0_next - m0_now
    d1 = m1_next - m1_now
    
    if abs(d0 - d1) > 0.01:
        # What caused the difference at step s?
        act0 = step_now[0].get('action') or {}
        act1 = step_now[1].get('action') or {}
        diff_events.append((s, d0, d1, d0 - d1, m0_next - m1_next, act0.get('market'), act1.get('market')))

print(f'Total divergence steps: {len(diff_events)}')
# Group divergence steps by Day
by_day = defaultdict(float)
for ev in diff_events:
    s = ev[0]
    by_day[s // 24] += ev[3]

print(f"{'Day':5s} | {'Net Cash Delta (A7 - Dm)':25s}")
print('-' * 35)
tot = 0
for d in sorted(by_day.keys()):
    tot += by_day[d]
    print(f"{d:5d} | {by_day[d]:+25.1f} | Cumulative: {tot:+10.1f}")
