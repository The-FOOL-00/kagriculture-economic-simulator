import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
team_names = data['info']['TeamNames']
rewards = data['rewards']

print(f"Match: Player 0: {team_names[0]} (${rewards[0]}) vs Player 1: {team_names[1]} (${rewards[1]})")

# Let's inspect both players
for p_idx in [1, 0]:
    p_name = team_names[p_idx]
    print("\n" + "=" * 80)
    print(f"ANALYSIS OF PLAYER {p_idx}: {p_name} (Reward: ${rewards[p_idx]})")
    print("=" * 80)
    
    # Track actions and state changes
    total_wheat_bought = 0
    total_wheat_cost = 0
    total_sales = {}
    total_seeds_bought = {}
    total_animals_bought = {}
    quad_unlock_steps = []
    
    prev_quads = []
    prev_pastures = 0
    prev_animals = {'COW': 0, 'SHEEP': 0, 'GOOSE': 0}
    prev_money = 0
    
    step_history = []
    
    for s_idx, step_entry in enumerate(steps):
        p_data = step_entry[p_idx]
        obs = p_data.get('observation', {})
        farms = obs.get('farms', [])
        farm = farms[p_idx] if len(farms) > p_idx else {}
        private = obs.get('private', {})
        shed = private.get('shed', {})
        money = float(farm.get('money', 0) or 0)
        quads = farm.get('unlocked_quadrants', [])
        market = obs.get('market', {})
        m_prices = market.get('prices', {})
        town = obs.get('town', {})
        shops = town.get('unlocked_shops', [])
        
        # Tiles & Livestock
        cows = 0
        sheep = 0
        geese = 0
        pastures = 0
        crops = {}
        soils = 0
        grass = 0
        
        for row in farm.get('tiles', []):
            for tile in row:
                if isinstance(tile, dict):
                    kind = tile.get('kind')
                    if kind == 'PASTURE':
                        pastures += 1
                    elif kind == 'PLANT':
                        c_name = tile.get('crop', 'UNKNOWN')
                        crops[c_name] = crops.get(c_name, 0) + 1
                    animal = tile.get('animal')
                    if animal == 'COW':
                        cows += 1
                    elif animal == 'SHEEP':
                        sheep += 1
                    elif animal == 'GOOSE':
                        geese += 1
                elif tile == 'SOIL':
                    soils += 1
                elif tile == 'GRASS':
                    grass += 1
                    
        hands_list = farm.get('hands', [])
        workers = len(hands_list) + (1 if farm.get('farmer') else 0)
        
        action = p_data.get('action', {})
        m_actions = action.get('market', []) if isinstance(action, dict) else []
        town_act = action.get('town', []) if isinstance(action, dict) else []
        farm_act = action.get('farm', []) if isinstance(action, dict) else []
        farmer_act = action.get('farmer', []) if isinstance(action, dict) else []
        hands_act = action.get('hands', []) if isinstance(action, dict) else []
        
        action_events = []
        
        if len(quads) > len(prev_quads):
            new_q = [q for q in quads if q not in prev_quads]
            action_events.append(f"QUAD_UNLOCK {new_q} (now {quads})")
            quad_unlock_steps.append((s_idx, new_q))
            
        if pastures != prev_pastures:
            action_events.append(f"PASTURE {prev_pastures}->{pastures}")
            
        if cows != prev_animals['COW']:
            action_events.append(f"COW {prev_animals['COW']}->{cows}")
            
        if sheep != prev_animals['SHEEP']:
            action_events.append(f"SHEEP {prev_animals['SHEEP']}->{sheep}")
            
        # Parse market actions
        for ma in m_actions:
            if isinstance(ma, list) and len(ma) >= 3:
                op, item, qty = ma[0], ma[1], int(ma[2])
                p = float(m_prices.get(item, 0))
                val = qty * p
                if op == 'BUY_PRODUCT' and item == 'WHEAT':
                    total_wheat_bought += qty
                    total_wheat_cost += val
                    action_events.append(f"BUY_PRODUCT WHEAT x{qty} @ ${p:.1f}")
                elif op == 'SELL_PRODUCT':
                    total_sales[item] = total_sales.get(item, 0) + qty
                    action_events.append(f"SELL_PRODUCT {item} x{qty} @ ${p:.1f} (+${val:.1f})")
                elif op == 'BUY_SEED':
                    total_seeds_bought[item] = total_seeds_bought.get(item, 0) + qty
                    action_events.append(f"BUY_SEED {item} x{qty} @ ${p:.1f}")
                elif op == 'BUY_ANIMAL':
                    total_animals_bought[item] = total_animals_bought.get(item, 0) + qty
                    action_events.append(f"BUY_ANIMAL {item} x{qty}")
                else:
                    action_events.append(f"MARKET {ma}")
                    
        # Check town actions (unlocking shops, buying quads, hiring workers)
        if town_act:
            action_events.append(f"TOWN_ACT: {town_act}")
        if farm_act:
            action_events.append(f"FARM_ACT: {farm_act}")
            
        step_history.append({
            'step': s_idx,
            'money': money,
            'workers': workers,
            'pastures': pastures,
            'cows': cows,
            'sheep': sheep,
            'crops': crops,
            'shed': shed,
            'quads': list(quads),
            'events': action_events
        })
        
        prev_quads = quads
        prev_pastures = pastures
        prev_animals = {'COW': cows, 'SHEEP': sheep, 'GOOSE': geese}
        prev_money = money

    print(f"Summary for {p_name}:")
    print(f"  Quadrant unlocks: {quad_unlock_steps}")
    print(f"  Total WHEAT bought: {total_wheat_bought} units (${total_wheat_cost:.1f})")
    print(f"  Total Sales: {total_sales}")
    print(f"  Total Seeds Bought: {total_seeds_bought}")
    print(f"  Total Animals Bought: {total_animals_bought}")
    
    # Let's print milestones:
    print("\n  Key Step Milestones:")
    for row in step_history:
        s = row['step']
        if s in [0, 50, 100, 122, 123, 150, 151, 198, 199, 200, 201, 250, 266, 300, 350, 400, 450, 500, 550, 600, 650, 700, 719] or len(row['events']) > 0:
            events_str = "; ".join(row['events']) if row['events'] else "none"
            crops_str = ", ".join(f"{k}:{v}" for k, v in row['crops'].items()) if row['crops'] else "none"
            shed_str = ", ".join(f"{k}:{v}" for k, v in row['shed'].items() if v > 0) if row['shed'] else "empty"
            if len(row['events']) > 0 or s % 50 == 0 or s in [122, 151, 198, 200, 266, 719]:
                print(f"  [Step {s:3d}] Cash: ${row['money']:8.1f} | Workers: {row['workers']:2d} | Quads: {row['quads']} | Pastures: {row['pastures']:2d} | Cows: {row['cows']:2d} | Sheep: {row['sheep']:2d} | Crops: {crops_str} | Shed: {shed_str} | Ev: {events_str}")

