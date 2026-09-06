import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/replays/Whyme_Labs_104824599.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
team_names = data['info']['TeamNames']
rewards = data['rewards']

print(f"Match: {team_names[0]} (${rewards[0]}) vs {team_names[1]} (${rewards[1]})")

for p_idx in [0, 1]:
    p_name = team_names[p_idx]
    p_reward = rewards[p_idx]
    print(f"\n=======================================================")
    print(f"PLAYER {p_idx}: {p_name} (${p_reward})")
    print(f"=======================================================")
    
    total_wheat_bought = 0
    total_wheat_cost = 0
    total_milk_sold = 0
    total_milk_rev = 0
    total_melon_sold = 0
    total_straw_sold = 0
    total_wool_sold = 0
    
    for s_idx in range(len(steps)):
        p_data = steps[s_idx][p_idx]
        obs = p_data.get('observation', {})
        farm = obs.get('farms', [{}, {}])[p_idx] if 'farms' in obs else {}
        private = obs.get('private', {})
        shed = private.get('shed', {})
        money = farm.get('money', 0)
        quads = farm.get('unlocked_quadrants', [])
        market = obs.get('market', {})
        m_prices = market.get('prices', {})
        town = obs.get('town', {})
        
        # count cows, sheep, workers
        cows = 0
        sheep = 0
        pastures = 0
        for row in farm.get('tiles', []):
            for tile in row:
                if isinstance(tile, dict):
                    if tile.get('kind') == 'PASTURE':
                        pastures += 1
                    if tile.get('animal') == 'COW':
                        cows += 1
                    elif tile.get('animal') == 'SHEEP':
                        sheep += 1
        workers = len(farm.get('hands', [])) + (1 if farm.get('farmer') else 0)
        
        action = p_data.get('action', {})
        m_actions = action.get('market', []) if isinstance(action, dict) else []
        
        # Track sales and purchases
        for ma in m_actions:
            if isinstance(ma, list) and len(ma) >= 3:
                op, item, qty = ma[0], ma[1], int(ma[2])
                p = m_prices.get(item, 0)
                if op == 'BUY_PRODUCT' and item == 'WHEAT':
                    total_wheat_bought += qty
                    total_wheat_cost += qty * p
                elif op == 'SELL':
                    if item == 'MILK':
                        total_milk_sold += qty
                        total_milk_rev += qty * p
                    elif item == 'MELON':
                        total_melon_sold += qty
                    elif item == 'STRAWBERRY':
                        total_straw_sold += qty
                    elif item == 'WOOL':
                        total_wool_sold += qty
        
        day = s_idx // 24
        hour = s_idx % 24
        
        # Print if major event: Q buy, market trade, cow buy, or step 120-260 every 6 hours
        is_q_buy = any(isinstance(a, list) and 'BUY_LAND' in a for a in m_actions)
        is_cow_buy = any(isinstance(a, list) and 'BUY_ANIMAL' in a and 'COW' in a for a in m_actions)
        is_trade = len(m_actions) > 0
        
        if is_q_buy or is_cow_buy or (120 <= s_idx <= 264 and (is_trade or hour % 6 == 0)):
            print(f"T{s_idx:3d} (D{day:02d} H{hour:02d}) | Cash: ${money:7.1f} | Q: {len(quads)} | Cows: {cows:2d} | Sheep: {sheep:2d} | Past: {pastures:2d} | W: {workers:2d} | Shed M:{shed.get('MILK',0):2d} W:{shed.get('WHEAT',0):3d} | WP: ${m_prices.get('WHEAT',0)} MP: ${m_prices.get('MILK',0)} | Act: {m_actions}")

    print(f"\nTOTALS for {p_name}:")
    print(f"  Wheat Bought: {total_wheat_bought} (Cost: ${total_wheat_cost:,.1f})")
    print(f"  Milk Sold: {total_milk_sold} (Revenue: ${total_milk_rev:,.1f})")
    print(f"  Melon Sold: {total_melon_sold}")
    print(f"  Strawberry Sold: {total_straw_sold}")
    print(f"  Wool Sold: {total_wool_sold}")
