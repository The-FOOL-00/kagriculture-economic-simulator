import sys
import os
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))
from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

def trace_late():
    seed = 941215
    q_agent = BaseQ50Agent(50)
    env_q = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed})
    steps_q = env_q.run([q_agent, 'starter'])

    c_agent = L_MinimalAgent(50)
    env_c = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed})
    steps_c = env_c.run([c_agent, 'starter'])

    # Track sales per day
    def get_market_sales(steps):
        sales_by_day = [{} for _ in range(30)]
        for s in range(len(steps)):
            d = s // 24
            m = steps[s][0]['action'].get('market', [])
            for o in m:
                if len(o) >= 3 and o[0] == 'SELL':
                    comm = o[1]
                    qty = o[2]
                    sales_by_day[d][comm] = sales_by_day[d].get(comm, 0) + qty
        return sales_by_day

    sales_q = get_market_sales(steps_q)
    sales_c = get_market_sales(steps_c)

    print(f"Daily Strawberry Sales on Seed {seed}:")
    for d in range(20, 30):
        q_s = sales_q[d].get('STRAWBERRY', 0)
        c_s = sales_c[d].get('STRAWBERRY', 0)
        q_m = sales_q[d].get('MELON', 0)
        c_m = sales_c[d].get('MELON', 0)
        print(f"  Day {d:2d}: Straw Q={q_s:2d} C={c_s:2d} (Diff {c_s - q_s:+2d}) | Melon Q={q_m:2d} C={c_m:2d} (Diff {c_m - q_m:+2d})")

    # Look at plant states at Day 29 Step 719
    def count_plants(tiles):
        straws = 0
        melons = 0
        unharvested_straw_yield = 0
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if isinstance(t, dict):
                    if t.get('crop') == 'STRAWBERRY':
                        straws += 1
                        unharvested_straw_yield += t.get('yield_units', 0)
                    elif t.get('crop') == 'MELON':
                        melons += 1
        return straws, melons, unharvested_straw_yield

    tiles_q = steps_q[-1][0]['observation']['farms'][0]['tiles']
    tiles_c = steps_c[-1][0]['observation']['farms'][0]['tiles']
    sq, mq, yq = count_plants(tiles_q)
    sc, mc, yc = count_plants(tiles_c)
    print(f"\nFinal Crop Standing at Step 719:")
    print(f"  Q50:       Strawberries={sq}, Melons={mq}, Unharvested Straw Yield={yq}")
    print(f"  Candidate: Strawberries={sc}, Melons={mc}, Unharvested Straw Yield={yc}")

    # Check worker inventories at step 719
    inv_q = steps_q[-1][0]['observation']['private']['inventories']
    inv_c = steps_c[-1][0]['observation']['private']['inventories']
    print(f"  Q50 Worker Inventories: {inv_q}")
    print(f"  Cand Worker Inventories: {inv_c}")

if __name__ == '__main__':
    trace_late()
