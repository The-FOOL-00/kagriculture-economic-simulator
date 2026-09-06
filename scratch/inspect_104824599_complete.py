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

# Analyze both players, especially Player 1 (Crop Dusta, $148,060)
for p_idx in [1, 0]:
    p_name = team_names[p_idx]
    print("=" * 80)
    print(f"DETAILED STEP-BY-STEP FORENSIC AUDIT: {p_name} (Player {p_idx}) Final: ${rewards[p_idx]}")
    print("=" * 80)
    
    prev_money = 0
    prev_quads = []
    prev_pastures = 0
    prev_cows = 0
    prev_sheep = 0
    prev_workers = 0
    prev_shed = {}
    prev_shops = []
    
    trade_summary = {
        'buy_wheat_qty': 0, 'buy_wheat_cost': 0,
        'sell_milk_qty': 0, 'sell_milk_rev': 0,
        'sell_wool_qty': 0, 'sell_wool_rev': 0,
        'sell_melon_qty': 0, 'sell_melon_rev': 0,
        'sell_straw_qty': 0, 'sell_straw_rev': 0,
        'sell_fert_qty': 0, 'sell_fert_rev': 0,
        'buy_seeds': {},
        'buy_animals': {},
        'buy_workers': 0,
        'buy_worker_cost': 0,
        'shop_unlocks': [],
        'quad_unlocks': [],
    }
    
    events = []
    
    for s_idx in range(len(steps)):
        step_entry = steps[s_idx]
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
        
        # Check action executed in this step
        action = p_data.get('action', {})
        m_actions = action.get('market', []) if isinstance(action, dict) else []
        town_act = action.get('town', []) if isinstance(action, dict) else []
        farm_act = action.get('farm', []) if isinstance(action, dict) else []
        farmer_act = action.get('farmer', []) if isinstance(action, dict) else []
        hands_act = action.get('hands', []) if isinstance(action, dict) else []
        
        # Detect unlocks
        if len(quads) > len(prev_quads):
            new_q = [q for q in quads if q not in prev_quads]
            events.append((s_idx, f"QUADRANT UNLOCK: {new_q} (Total: {quads}), Money: ${money:.1f}"))
            trade_summary['quad_unlocks'].append((s_idx, new_q, money))
            
        if len(shops) > len(prev_shops):
            new_s = [s for s in shops if s not in prev_shops]
            events.append((s_idx, f"SHOP UNLOCK: {new_s} (Total: {shops}), Money: ${money:.1f}"))
            trade_summary['shop_unlocks'].append((s_idx, new_s, money))
            
        if pastures > prev_pastures:
            events.append((s_idx, f"PASTURE BUILT: {prev_pastures} -> {pastures}, Money: ${money:.1f}"))
            
        if cows > prev_cows:
            events.append((s_idx, f"COW ADDED: {prev_cows} -> {cows}, Money: ${money:.1f}"))
            
        if sheep > prev_sheep:
            events.append((s_idx, f"SHEEP ADDED: {prev_sheep} -> {sheep}, Money: ${money:.1f}"))
            
        if workers > prev_workers:
            events.append((s_idx, f"WORKER HIRED: {prev_workers} -> {workers}, Money: ${money:.1f}"))
            
        # Parse market actions
        for ma in m_actions:
            if isinstance(ma, list) and len(ma) >= 3:
                op, item, qty = ma[0], ma[1], int(ma[2])
                p = float(m_prices.get(item, 0))
                val = qty * p
                if op == 'BUY_PRODUCT' and item == 'WHEAT':
                    trade_summary['buy_wheat_qty'] += qty
                    trade_summary['buy_wheat_cost'] += val
                    events.append((s_idx, f"BUY WHEAT: {qty} units @ ${p:.2f} = ${val:.1f} (Cum: {trade_summary['buy_wheat_qty']})"))
                elif op == 'SELL_PRODUCT' and item == 'MILK':
                    trade_summary['sell_milk_qty'] += qty
                    trade_summary['sell_milk_rev'] += val
                    events.append((s_idx, f"SELL MILK: {qty} units @ ${p:.2f} = ${val:.1f} (Cum: {trade_summary['sell_milk_qty']})"))
                elif op == 'SELL_PRODUCT' and item == 'WOOL':
                    trade_summary['sell_wool_qty'] += qty
                    trade_summary['sell_wool_rev'] += val
                    events.append((s_idx, f"SELL WOOL: {qty} units @ ${p:.2f} = ${val:.1f}"))
                elif op == 'SELL_PRODUCT' and item == 'MELON':
                    trade_summary['sell_melon_qty'] += qty
                    trade_summary['sell_melon_rev'] += val
                    events.append((s_idx, f"SELL MELON: {qty} units @ ${p:.2f} = ${val:.1f} (Cum: {trade_summary['sell_melon_qty']})"))
                elif op == 'SELL_PRODUCT' and item == 'STRAWBERRY':
                    trade_summary['sell_straw_qty'] += qty
                    trade_summary['sell_straw_rev'] += val
                    events.append((s_idx, f"SELL STRAWBERRY: {qty} units @ ${p:.2f} = ${val:.1f} (Cum: {trade_summary['sell_straw_qty']})"))
                elif op == 'SELL_PRODUCT' and item == 'FERTILIZER':
                    trade_summary['sell_fert_qty'] += qty
                    trade_summary['sell_fert_rev'] += val
                    events.append((s_idx, f"SELL FERTILIZER: {qty} units @ ${p:.2f} = ${val:.1f}"))
                elif op == 'BUY_SEED':
                    trade_summary['buy_seeds'][item] = trade_summary['buy_seeds'].get(item, 0) + qty
                    events.append((s_idx, f"BUY SEED: {qty} {item} @ ${p:.2f} = ${val:.1f}"))
                elif op == 'BUY_ANIMAL':
                    trade_summary['buy_animals'][item] = trade_summary['buy_animals'].get(item, 0) + qty
                    events.append((s_idx, f"BUY ANIMAL: {qty} {item}"))
                    
        # Periodic snapshot every 40 steps or on significant steps
        if s_idx in [0, 50, 100, 122, 150, 198, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 719]:
            print(f"Step {s_idx:3d} | Cash: ${money:8.1f} | Workers: {workers} | Quads: {len(quads)} {quads} | Pastures: {pastures:2d} | Cows: {cows:2d} | Sheep: {sheep:2d} | Crops: {crops} | Shed: {shed}")
            
        prev_money = money
        prev_quads = quads
        prev_pastures = pastures
        prev_cows = cows
        prev_sheep = sheep
        prev_workers = workers
        prev_shed = shed
        prev_shops = shops

    print("\n--- ALL KEY EVENTS ---")
    for step_num, ev in events:
        print(f"  Step {step_num:3d}: {ev}")
        
    print("\n--- TRADE TOTALS ---")
    print(json.dumps(trade_summary, indent=2))
    print("\n" + "#" * 80 + "\n")
