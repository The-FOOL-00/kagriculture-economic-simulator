import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def count_animals_and_workers(farm):
    cows = 0
    sheep = 0
    geese = 0
    for row in farm.get('tiles', []):
        for tile in row:
            if isinstance(tile, dict):
                animal = tile.get('animal')
                if animal == 'COW':
                    cows += 1
                elif animal == 'SHEEP':
                    sheep += 1
                elif animal == 'GOOSE':
                    geese += 1
    workers = len(farm.get('hands', [])) + (1 if farm.get('farmer') else 0)
    return cows, sheep, geese, workers

def analyze_episode(ep_id, fname):
    with open(fname, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    info = data.get('info', {})
    rewards = data.get('rewards', [])
    steps = data.get('steps', [])
    team_names = info.get('TeamNames', ['P0', 'P1'])
    
    print(f"\n{'='*70}")
    print(f"EPISODE {ep_id}: {team_names[0]} (${rewards[0]:,.1f}) vs {team_names[1]} (${rewards[1]:,.1f})")
    print(f"{'='*70}")
    
    # We will trace both players
    for p_idx in [0, 1]:
        p_name = team_names[p_idx]
        p_reward = rewards[p_idx]
        print(f"\n------------------------------------------------------------")
        print(f"Player {p_idx}: {p_name} (Final Reward: ${p_reward:,.1f})")
        print(f"------------------------------------------------------------")
        
        wheat_bought_total = 0
        wheat_spent_total = 0
        milk_sold_total = 0
        milk_revenue_total = 0
        wool_sold_total = 0
        wool_revenue_total = 0
        q_history = []
        
        for s_idx in range(len(steps)):
            step_data = steps[s_idx]
            p_data = step_data[p_idx]
            obs = p_data.get('observation', {})
            farm = obs.get('farms', [{}, {}])[p_idx] if 'farms' in obs else {}
            private = obs.get('private', {})
            shed = private.get('shed', {})
            money = farm.get('money', 0)
            quads = farm.get('unlocked_quadrants', [])
            market = obs.get('market', {})
            m_prices = market.get('prices', {})
            
            cows, sheep, geese, workers = count_animals_and_workers(farm)
            
            if len(quads) > len(q_history):
                q_history.append((len(quads), s_idx, s_idx//24, s_idx%24, money))
            
            action = p_data.get('action')
            if isinstance(action, dict):
                m_actions = action.get('market', [])
                if m_actions:
                    for ma in m_actions:
                        if isinstance(ma, list) and len(ma) >= 3:
                            op, item, qty = ma[0], ma[1], int(ma[2])
                            p = m_prices.get(item, 0)
                            if op == 'BUY_PRODUCT' and item == 'WHEAT':
                                wheat_bought_total += qty
                                wheat_spent_total += qty * p
                            elif op == 'SELL' and item == 'MILK':
                                milk_sold_total += qty
                                milk_revenue_total += qty * p
                            elif op == 'SELL' and item == 'WOOL':
                                wool_sold_total += qty
                                wool_revenue_total += qty * p
            
            # Print detailed trace on Days 4-11 when actions or key hours happen
            day = s_idx // 24
            hour = s_idx % 24
            if 4 <= day <= 11:
                # Check if there is market action or land buy or cow buy in action
                actions_str = str(action) if action else ""
                has_key_action = any(k in actions_str for k in ['MARKET', 'BUY_LAND', 'BUY_COW', 'BUY_PRODUCT', 'SELL'])
                if has_key_action or hour in (0, 12):
                    print(f"Step {s_idx:3d} (D{day:02d} H{hour:02d}) | Cash: ${money:7.1f} | Q: {len(quads)} | Cows: {cows:2d} | Sheep: {sheep:2d} | W: {workers:2d} | Shed Milk: {shed.get('MILK',0):2d} Wht: {shed.get('WHEAT',0):3d} | WP: ${m_prices.get('WHEAT',0)} MP: ${m_prices.get('MILK',0)} | Act: {action}")
        
        print(f"\nSummary for {p_name}:")
        print(f"  Quadrant Progression: {q_history}")
        print(f"  Total Wheat Bought: {wheat_bought_total} units (Cost: ${wheat_spent_total:,.1f})")
        print(f"  Total Milk Sold: {milk_sold_total} units (Revenue: ${milk_revenue_total:,.1f})")
        print(f"  Total Wool Sold: {wool_sold_total} units (Revenue: ${wool_revenue_total:,.1f})")
        print(f"  Final Cows: {cows}, Sheep: {sheep}, Geese: {geese}, Workers: {workers}")

for ep in ['104824599', '104821658', '104821944']:
    fname = f'scratch/replays/Whyme_Labs_{ep}.json'
    analyze_episode(ep, fname)
