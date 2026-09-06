import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
p_idx = 1 # Crop Dusta

# Track wheat balance over time:
# Wheat in shed, wheat bought, wheat harvested/sold, cows fed, sheep fed
wheat_events = []
wheat_in_shed = 0
prev_shed_wheat = 0

for s in range(len(steps)):
    obs = steps[s][p_idx]['observation']
    farm = obs['farms'][p_idx]
    shed = obs['private']['shed']
    shed_w = shed.get('WHEAT', 0)
    
    act = steps[s][p_idx].get('action', {})
    m_act = act.get('market', []) if isinstance(act, dict) else []
    
    w_bought = 0
    w_sold = 0
    for ma in m_act:
        if isinstance(ma, list) and len(ma) >= 3:
            if ma[0] == 'BUY_PRODUCT' and ma[1] == 'WHEAT':
                w_bought += int(ma[2])
            elif ma[0] in ['SELL_PRODUCT', 'SELL'] and ma[1] == 'WHEAT':
                w_sold += int(ma[2])
                
    # Estimate consumption by livestock
    cows = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
    sheep = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    
    if s % 24 == 0 or w_bought > 0 or w_sold > 0:
        wheat_events.append({
            'step': s,
            'day': s // 24,
            'hour': s % 24,
            'shed_wheat': shed_w,
            'wheat_bought': w_bought,
            'wheat_sold': w_sold,
            'cows': cows,
            'sheep': sheep
        })

print(f"Total wheat events: {len(wheat_events)}")
# Let's see daily summary
daily_wheat = {}
for we in wheat_events:
    d = we['day']
    if d not in daily_wheat:
        daily_wheat[d] = {'bought': 0, 'sold': 0, 'shed_start': we['shed_wheat'], 'cows': we['cows'], 'sheep': we['sheep']}
    daily_wheat[d]['bought'] += we['wheat_bought']
    daily_wheat[d]['sold'] += we['wheat_sold']
    daily_wheat[d]['cows'] = we['cows']
    daily_wheat[d]['sheep'] = we['sheep']

print(f"{'Day':>4} | {'Cows':>4} | {'Sheep':>5} | {'Bought':>7} | {'Sold':>6} | {'Daily Feed Req':>14}")
print("-" * 55)
for d, st in sorted(daily_wheat.items()):
    # In Kaggriculture: cows eat 1 wheat every 4 hours? Or every 8 hours?
    # Let's check rulebook: Cows eat 1 feed every X steps, sheep eat 1 feed every Y steps.
    feed_req = st['cows'] * (24 / 8) + st['sheep'] * (24 / 8) # approximate
    print(f"{d:4d} | {st['cows']:4d} | {st['sheep']:5d} | {st['bought']:7d} | {st['sold']:6d} | ~{feed_req:5.1f} units")
