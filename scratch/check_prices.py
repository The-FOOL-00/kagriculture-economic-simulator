import sys
import os
sys.path.insert(0, os.getcwd())
import kaggle_environments
from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

def check_straw_pricing(agent, name):
    env = kaggle_environments.make('kaggriculture', configuration={'seed': 1004})
    steps = env.run([agent, 'starter'])
    print(f"=== {name} Sales (Seed 1004) ===")
    for s_idx, s in enumerate(steps):
        act = s[0].get('action') or {}
        day = s[0]['observation']['day']
        hour = s[0]['observation']['hour']
        prices = s[0]['observation']['market']['prices']
        for m in act.get('market', []):
            if len(m) >= 3 and m[0] == 'SELL' and m[1] in ('STRAWBERRY', 'MILK'):
                item = m[1]
                qty = m[2]
                pr = prices.get(item)
                print(f"Day {day:2d}:H{hour:2d} (step {s_idx:3d}): SOLD {qty:2d} {item:<10} price={pr}")

check_straw_pricing(cl_baseline, 'Baseline')
check_straw_pricing(cl_gated, 'Gated')
