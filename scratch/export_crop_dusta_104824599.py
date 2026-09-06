import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
team_names = data['info']['TeamNames']
rewards = data['rewards']

p_idx = 1 # Crop Dusta ($148,060)
p_name = team_names[p_idx]

print(f"=== FULL AUDIT OF {p_name} (Player {p_idx}, Reward ${rewards[p_idx]}) ===")

full_log = []
prev_quads = []
prev_pastures = 0
prev_cows = 0
prev_sheep = 0
prev_workers = 0
prev_money = 0
prev_shed = {}

cumulative = {
    'wheat_bought_qty': 0,
    'wheat_bought_cost': 0,
    'seed_bought_qty': {},
    'seed_bought_cost': {},
    'animal_bought_qty': {},
    'animal_bought_cost': {},
    'product_sold_qty': {},
    'product_sold_rev': {},
    'quadrant_unlocks': [],
    'shop_unlocks': [],
    'pasture_built_steps': [],
}

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
    
    # Grid inventory
    pastures = 0
    cows = 0
    sheep = 0
    geese = 0
    crops = {}
    soils = 0
    grass = 0
    
    for r_idx, row in enumerate(farm.get('tiles', [])):
        for c_idx, tile in enumerate(row):
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
    
    step_events = []
    
    if len(quads) > len(prev_quads):
        new_q = [q for q in quads if q not in prev_quads]
        step_events.append(f"QUAD_UNLOCK {new_q} -> {quads}")
        cumulative['quadrant_unlocks'].append((s_idx, new_q, money))
        
    if pastures > prev_pastures:
        step_events.append(f"PASTURE_BUILT {prev_pastures} -> {pastures}")
        cumulative['pasture_built_steps'].append((s_idx, prev_pastures, pastures))
        
    if cows > prev_cows:
        step_events.append(f"COW_SPAWNED {prev_cows} -> {cows}")
    if sheep > prev_sheep:
        step_events.append(f"SHEEP_SPAWNED {prev_sheep} -> {sheep}")
        
    if workers > prev_workers:
        step_events.append(f"WORKER_COUNT {prev_workers} -> {workers}")
        
    for ma in m_actions:
        if isinstance(ma, list) and len(ma) >= 3:
            op, item, qty = ma[0], ma[1], int(ma[2])
            p = float(m_prices.get(item, 0))
            cost = qty * p
            if op == 'BUY_PRODUCT':
                if item == 'WHEAT':
                    cumulative['wheat_bought_qty'] += qty
                    cumulative['wheat_bought_cost'] += cost
                step_events.append(f"BUY_PRODUCT {item} x{qty} @ ${p:.1f} = ${cost:.1f}")
            elif op == 'SELL_PRODUCT' or op == 'SELL':
                cumulative['product_sold_qty'][item] = cumulative['product_sold_qty'].get(item, 0) + qty
                cumulative['product_sold_rev'][item] = cumulative['product_sold_rev'].get(item, 0) + cost
                step_events.append(f"SELL {item} x{qty} @ ${p:.1f} = +${cost:.1f}")
            elif op == 'BUY_SEED':
                cumulative['seed_bought_qty'][item] = cumulative['seed_bought_qty'].get(item, 0) + qty
                cumulative['seed_bought_cost'][item] = cumulative['seed_bought_cost'].get(item, 0) + cost
                step_events.append(f"BUY_SEED {item} x{qty} @ ${p:.1f} = ${cost:.1f}")
            elif op == 'BUY_ANIMAL':
                cumulative['animal_bought_qty'][item] = cumulative['animal_bought_qty'].get(item, 0) + qty
                cumulative['animal_bought_cost'][item] = cumulative['animal_bought_cost'].get(item, 0) + cost
                step_events.append(f"BUY_ANIMAL {item} x{qty} @ ${p:.1f} = ${cost:.1f}")
            else:
                step_events.append(f"MARKET {ma}")
                
    if town_act:
        step_events.append(f"TOWN_ACT {town_act}")
    if farm_act:
        step_events.append(f"FARM_ACT {farm_act}")
        
    full_log.append({
        'step': s_idx,
        'money': money,
        'workers': workers,
        'quads': list(quads),
        'pastures': pastures,
        'cows': cows,
        'sheep': sheep,
        'crops': crops,
        'shed': {k: v for k, v in shed.items() if v > 0},
        'events': step_events,
        'cum_wheat': cumulative['wheat_bought_qty']
    })
    
    prev_quads = quads
    prev_pastures = pastures
    prev_cows = cows
    prev_sheep = sheep
    prev_workers = workers
    prev_money = money
    prev_shed = shed

# Save structured full log to file
with open('scratch/crop_dusta_104824599_full_log.json', 'w') as f:
    json.dump({
        'cumulative': cumulative,
        'log': full_log
    }, f, indent=2)

print("Cumulative Totals:")
print(json.dumps(cumulative, indent=2))
