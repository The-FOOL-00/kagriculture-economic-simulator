import kaggle_environments
import os
import sys

sys.path.insert(0, os.getcwd())
from candidates.candidate_cl_economic_v1 import agent as cl_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def check_weed_yield_loss(agent, name):
    lost_units = []
    print(f"\nAuditing decay and weed yield loss for {name} across Seeds 1000-1009...")
    for seed in range(1000, 1010):
        env = kaggle_environments.make('kaggriculture', configuration={'seed': seed})
        steps = env.run([agent, 'starter'])
        seed_lost = 0
        decay_events = 0
        for s in range(1, len(steps)):
            pt = steps[s-1][0]['observation']['farms'][0]['tiles']
            ct = steps[s][0]['observation']['farms'][0]['tiles']
            for y in range(10):
                for x in range(10):
                    p = pt[y][x]
                    c = ct[y][x]
                    if isinstance(p, dict) and p.get('crop') == 'STRAWBERRY':
                        # Case A: became weed
                        if isinstance(c, dict) and c.get('kind') == 'WEED':
                            yu = p.get('yield_units', 0)
                            if yu > 0:
                                seed_lost += yu
                                print(f"  {name} Seed {seed} step {s} (D{s//24}:H{s%24}): Strawberry at ({x},{y}) with {yu} yu turned into WEED!")
                        # Case B: lifespan decay (decremented yu without harvest)
                        elif isinstance(c, dict) and c.get('crop') == 'STRAWBERRY':
                            act = steps[s][0].get('action') or {}
                            workers = [steps[s-1][0]['observation']['farms'][0]['farmer']] + (steps[s-1][0]['observation']['farms'][0]['hands'] or [])
                            all_acts = ([act.get('farmer')] if act.get('farmer') else []) + (act.get('hands', []) or [])
                            harvested = any(w_act and w_act[0] == 'HARVEST' and w_pos == [x, y] for w_pos, w_act in zip(workers, all_acts))
                            if not harvested and p.get('yield_units', 0) > c.get('yield_units', 0):
                                diff = p['yield_units'] - c['yield_units']
                                seed_lost += diff
                                decay_events += 1
                                print(f"  {name} Seed {seed} step {s} (D{s//24}:H{s%24}): Strawberry at ({x},{y}) lost {diff} yu to lifespan decay! mls={p.get('max_lifespan_step')}")
        lost_units.append(seed_lost)
    print(f"{name} Lost units to decay/weed: mean={sum(lost_units)/len(lost_units):.2f}, per seed={lost_units}")
    return lost_units

cl_lost = check_weed_yield_loss(cl_agent, 'CL')
v2_lost = check_weed_yield_loss(v2_agent, 'V2')
