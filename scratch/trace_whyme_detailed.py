import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

episodes = ['104824599', '104821658', '104821944']

for ep in episodes:
    fname = f'scratch/replays/Whyme_Labs_{ep}.json'
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error opening {fname}: {e}")
        continue
    
    info = data.get('info', {})
    rewards = data.get('rewards', [])
    steps = data.get('steps', [])
    
    team_names = info.get('TeamNames', [])
    
    print(f"\n==================================================")
    print(f"EPISODE {ep} (Total Steps: {len(steps)})")
    print(f"Team Names: {team_names}")
    print(f"Rewards: {rewards}")
    print(f"==================================================")
    
    for p_idx in [0, 1]:
        p_name = team_names[p_idx] if p_idx < len(team_names) else f"Player {p_idx}"
        p_reward = rewards[p_idx] if p_idx < len(rewards) else None
        print(f"\n--- Player {p_idx}: {p_name} (Final Reward: {p_reward}) ---")
        
        for s_idx in range(len(steps)):
            step_data = steps[s_idx]
            obs = step_data[0]['observation'] if 'observation' in step_data[0] else None
            action = step_data[p_idx].get('action', None)
            
            if obs and 'farms' in obs and p_idx < len(obs['farms']):
                farm = obs['farms'][p_idx]
                day = s_idx // 24
                hour = s_idx % 24
                
                actions = action if isinstance(action, list) else []
                has_market_action = any('MARKET' in str(a) or 'BUY_LAND' in str(a) or 'BUY_COW' in str(a) or 'SELL' in str(a) or 'BUY' in str(a) for a in actions)
                
                if 4 <= day <= 11 and (has_market_action or hour % 12 == 0):
                    money = farm.get('money', 0)
                    inventory = farm.get('inventory', {})
                    quadrants = farm.get('unlocked_quadrants', [])
                    cows = len(farm.get('cows', []))
                    sheep = len(farm.get('sheep', []))
                    workers = len(farm.get('workers', []))
                    
                    market = obs.get('market', {})
                    wheat_price = market.get('wheat', {}).get('price', None) if 'wheat' in market else None
                    milk_price = market.get('milk', {}).get('price', None) if 'milk' in market else None
                    
                    town = obs.get('town', {})
                    unlocked_shops = town.get('unlocked_shops', [])
                    
                    print(f"Step {s_idx:3d} (D{day:02d} H{hour:02d}) | Cash: ${money:7.1f} | Q: {len(quadrants)} | Cows: {cows:2d} | Sheep: {sheep:2d} | W: {workers:2d} | Milk: {inventory.get('milk', 0):3d} | Wheat: {inventory.get('wheat', 0):4d} | WPrice: {wheat_price} | MPrice: {milk_price} | Act: {actions}")
