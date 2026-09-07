import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def profile_run(agent_fn, agent_name, seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    starter_fn = kaggle_environments.environments['kaggriculture']['agents']['starter']
    env.run([agent_fn, starter_fn])
    
    sales = {}
    purchases = {}
    actions_count = {"MOVE": 0, "HARVEST": 0, "WATER": 0, "PLANT": 0, "FEED": 0, "CARE": 0, "PICKUP": 0, "PLACE": 0, "PASS": 0, "OTHER": 0}
    
    prev_money = 3000.0
    daily_cash = []
    
    for s_idx, step_data in enumerate(env.steps):
        if s_idx == 0:
            continue
        p0_data = step_data[0]
        act0 = p0_data.get('action') or {}
        obs0 = p0_data.get('observation') or {}
        f0 = (obs0.get('farms') or [{}])[0]
        cur_money = f0.get('money', 0.0)
        
        if s_idx % 24 == 0:
            daily_cash.append(cur_money)
            
        m_orders = act0.get('market', []) if isinstance(act0, dict) else []
        for o in m_orders:
            if not isinstance(o, list) or len(o) == 0: continue
            cmd = o[0]
            if cmd == 'SELL' and len(o) >= 3:
                sales[o[1]] = sales.get(o[1], 0) + int(o[2])
            elif cmd == 'BUY_PRODUCT' and len(o) >= 3:
                purchases[o[1]] = purchases.get(o[1], 0) + int(o[2])
            elif cmd == 'BUY_SEED' and len(o) >= 3:
                purchases[f"SEED_{o[1]}"] = purchases.get(f"SEED_{o[1]}", 0) + int(o[2])
            elif cmd == 'BUY_ANIMAL' and len(o) >= 3:
                purchases[f"ANIMAL_{o[1]}"] = purchases.get(f"ANIMAL_{o[1]}", 0) + int(o[2])
            elif cmd == 'BUY_LAND':
                purchases['LAND'] = purchases.get('LAND', 0) + 1
            elif cmd == 'HIRE':
                purchases['HIRE'] = purchases.get('HIRE', 0) + 1
                
        all_units = [act0.get('farmer', ['PASS'])] + (act0.get('hands', []) if isinstance(act0, dict) else [])
        for u_act in all_units:
            if not u_act:
                actions_count["PASS"] += 1
                continue
            op = u_act[0] if isinstance(u_act, (list, tuple)) else str(u_act)
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                actions_count["MOVE"] += 1
            elif op in actions_count:
                actions_count[op] += 1
            else:
                actions_count["OTHER"] += 1

    final_reward = env.steps[-1][0]['reward']
    print(f"=== {agent_name} (Seed {seed}) Final Reward: ${final_reward:,.1f} ===")
    print("Action counts:", actions_count)
    print("Market Sales:", sales)
    print("Market Purchases:", purchases)
    
    final_farm = env.steps[-1][0]['observation']['farms'][0]
    tiles = final_farm.get('tiles', [])
    cows = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get('animal') == 'COW')
    sheep = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    pastures = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get('kind') == 'PASTURE')
    quads = final_farm.get('unlocked_quadrants', [])
    hands = len(final_farm.get('hands', []))
    print(f"Final Farm State: Quads={quads}, Pastures={pastures}, Cows={cows}, Sheep={sheep}, Hands={hands}")
    print(f"Daily cash milestones (every 24 steps): {[round(x) for x in daily_cash]}")
    print()
    return {
        "reward": final_reward,
        "actions": actions_count,
        "sales": sales,
        "purchases": purchases,
        "quads": quads,
        "pastures": pastures,
        "cows": cows,
        "sheep": sheep,
        "hands": hands,
        "daily_cash": daily_cash
    }

if __name__ == '__main__':
    v2_res = profile_run(v2_agent, "V2 Baseline", 42)
    prime_res = profile_run(prime_agent, "CL-Aethel Prime", 42)
