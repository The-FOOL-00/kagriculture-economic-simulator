import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
team_names = data['info']['TeamNames']
rewards = data['rewards']

print(f"Match: {team_names[0]} (${rewards[0]}) vs {team_names[1]} (${rewards[1]})")

# Player 1 is Crop Dusta ($148,060)
p_idx = 1
p_name = team_names[p_idx]

print(f"Deep Forensic Audit of {p_name} (Player {p_idx}) across 720 Steps\n")

timeline = []
cum_wheat_bought = 0
cum_wheat_cost = 0
cum_milk_sold = 0
cum_milk_rev = 0
cum_wool_sold = 0
cum_wool_rev = 0
cum_melon_sold = 0
cum_melon_rev = 0
cum_straw_sold = 0
cum_straw_rev = 0
cum_fert_sold = 0
cum_fert_rev = 0

for s_idx in range(len(steps)):
    step_entry = steps[s_idx]
    p_data = step_entry[p_idx]
    obs = p_data.get('observation', {})
    farm = obs.get('farms', [{}, {}])[p_idx] if 'farms' in obs else {}
    private = obs.get('private', {})
    shed = private.get('shed', {})
    money = float(farm.get('money', 0) or 0)
    quads = farm.get('unlocked_quadrants', [])
    market = obs.get('market', {})
    m_prices = market.get('prices', {})
    town = obs.get('town', {})
    shops = town.get('unlocked_shops', [])
    
    # Tile analysis
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
                
    workers = len(farm.get('hands', [])) + (1 if farm.get('farmer') else 0)
    
    action = p_data.get('action', {})
    m_actions = action.get('market', []) if isinstance(action, dict) else []
    farmer_act = action.get('farmer', []) if isinstance(action, dict) else []
    hands_act = action.get('hands', []) if isinstance(action, dict) else []
    
    # Track market trade specifics
    step_wheat_bought = 0
    step_milk_sold = 0
    step_melon_sold = 0
    step_straw_sold = 0
    step_wool_sold = 0
    step_fert_sold = 0
    
    for ma in m_actions:
        if isinstance(ma, list) and len(ma) >= 3:
            op, item, qty = ma[0], ma[1], int(ma[2])
            p = float(m_prices.get(item, 0))
            if op == 'BUY_PRODUCT' and item == 'WHEAT':
                step_wheat_bought += qty
                cum_wheat_bought += qty
                cum_wheat_cost += qty * p
            elif op == 'SELL':
                if item == 'MILK':
                    step_milk_sold += qty
                    cum_milk_sold += qty
                    cum_milk_rev += qty * p
                elif item == 'MELON':
                    step_melon_sold += qty
                    cum_melon_sold += qty
                    cum_melon_rev += qty * p
                elif item == 'STRAWBERRY':
                    step_straw_sold += qty
                    cum_straw_sold += qty
                    cum_straw_rev += qty * p
                elif item == 'WOOL':
                    step_wool_sold += qty
                    cum_wool_sold += qty
                    cum_wool_rev += qty * p
                elif item == 'FERTILIZER':
                    step_fert_sold += qty
                    cum_fert_sold += qty
                    cum_fert_rev += qty * p
                    
    timeline.append({
        'step': s_idx,
        'day': s_idx // 24,
        'hour': s_idx % 24,
        'money': money,
        'quads': len(quads),
        'cows': cows,
        'sheep': sheep,
        'workers': workers,
        'pastures': pastures,
        'crops': crops,
        'soils': soils,
        'shed_milk': shed.get('MILK', 0),
        'shed_wheat': shed.get('WHEAT', 0),
        'shed_melon': shed.get('MELON', 0),
        'shed_straw': shed.get('STRAWBERRY', 0),
        'shed_wool': shed.get('WOOL', 0),
        'shed_fert': shed.get('FERTILIZER', 0),
        'wheat_price': m_prices.get('WHEAT', 0),
        'milk_price': m_prices.get('MILK', 0),
        'melon_price': m_prices.get('MELON', 0),
        'straw_price': m_prices.get('STRAWBERRY', 0),
        'wool_price': m_prices.get('WOOL', 0),
        'm_actions': m_actions,
        'farmer_act': farmer_act,
        'hands_act': hands_act,
        'shops': list(shops),
        'cum_wheat_bought': cum_wheat_bought,
        'cum_wheat_cost': cum_wheat_cost,
        'cum_milk_sold': cum_milk_sold,
        'cum_milk_rev': cum_milk_rev,
        'cum_melon_sold': cum_melon_sold,
        'cum_straw_sold': cum_straw_sold,
    })

# Print high-density summary of key transitions
print(f"{'Step':>4} | {'Day:Hr':>6} | {'Cash ($)':>8} | {'Q':>1} | {'Cows':>4} | {'Past':>4} | {'W':>2} | {'Crops Distribution':<30} | {'Shed (M/Wh/Ml/St/Wl)':<20} | {'Market Actions / Key Events'}")
print("-" * 140)

last_q = 1
last_cows = 0
last_past = 0

for t in timeline:
    s = t['step']
    m_acts = t['m_actions']
    has_trade = len(m_acts) > 0
    q_changed = t['quads'] != last_q
    cow_changed = t['cows'] != last_cows
    past_changed = t['pastures'] != last_past
    
    last_q = t['quads']
    last_cows = t['cows']
    last_past = t['pastures']
    
    # Print if major event or periodic checkpoint
    if q_changed or cow_changed or past_changed or has_trade or (s % 24 == 0) or s in [122, 198, 199, 200, 201, 264, 266, 360, 500, 680, 712, 719]:
        crops_str = ", ".join(f"{k}:{v}" for k, v in t['crops'].items()) if t['crops'] else "None"
        shed_str = f"M:{t['shed_milk']} Wh:{t['shed_wheat']} Ml:{t['shed_melon']} St:{t['shed_straw']} Wl:{t['shed_wool']}"
        acts_str = str(m_acts) if m_acts else ""
        if q_changed:
            acts_str += f" [UNLOCKED Q{t['quads']}]"
        print(f"{s:4d} | D{t['day']:02d}:H{t['hour']:02d} | ${t['money']:8.1f} | {t['quads']:1d} | {t['cows']:4d} | {t['pastures']:4d} | {t['workers']:2d} | {crops_str:<30} | {shed_str:<20} | {acts_str}")

print("\n" + "=" * 140)
print("FINAL ECONOMIC TOTALS FOR CROP DUSTA:")
print("=" * 140)
print(f"Final Reward:                  ${timeline[-1]['money']:,.1f}")
print(f"Total Wheat Bought:            {cum_wheat_bought} units (Total Cost: ${cum_wheat_cost:,.1f}, Avg Price: ${cum_wheat_cost/max(1,cum_wheat_bought):.2f})")
print(f"Total Milk Sold:               {cum_milk_sold} units (Total Revenue: ${cum_milk_rev:,.1f}, Avg Price: ${cum_milk_rev/max(1,cum_milk_sold):.2f})")
print(f"Total Wool Sold:               {cum_wool_sold} units (Total Revenue: ${cum_wool_rev:,.1f})")
print(f"Total Melon Sold:              {cum_melon_sold} units (Total Revenue: ${cum_melon_rev:,.1f})")
print(f"Total Strawberry Sold:         {cum_straw_sold} units (Total Revenue: ${cum_straw_rev:,.1f})")
print(f"Total Fertilizer Sold:         {cum_fert_sold} units (Total Revenue: ${cum_fert_rev:,.1f})")
print(f"Net Livestock Cash Flow:       ${cum_milk_rev + cum_wool_rev - cum_wheat_cost:,.1f}")
print(f"Final Active Assets:           {timeline[-1]['cows']} Cows, {timeline[-1]['sheep']} Sheep, {timeline[-1]['pastures']} Pastures, {timeline[-1]['workers']} Workers, {timeline[-1]['quads']} Quadrants")
print("=" * 140)
