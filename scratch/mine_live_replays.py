import os, json, glob
from collections import defaultdict, Counter

replay_dir = 'replays'
replay_files = sorted(glob.glob(os.path.join(replay_dir, '*.json')))
print(f"Found {len(replay_files)} replay files in {replay_dir}/")

# Also check root replays
root_replays = glob.glob('*replay*.json')
print(f"Found {len(root_replays)} replay files in root: {root_replays}")

all_replays = replay_files + root_replays

replay_data = []

for rpath in all_replays:
    try:
        with open(rpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metadata
        steps = data.get('steps', [])
        if not steps:
            continue
        
        # Check initial and final steps
        init_step = steps[0]
        final_step = steps[-1]
        
        # Rewards
        r0 = final_step[0].get('reward', 0)
        r1 = final_step[1].get('reward', 0)
        
        # Extract actions across turns 0-50 for both players
        p0_actions_0_50 = []
        p1_actions_0_50 = []
        
        # Extract animal purchases, worker hires, crops planted
        p0_animals = Counter()
        p1_animals = Counter()
        p0_crops = Counter()
        p1_crops = Counter()
        p0_workers_max = 1
        p1_workers_max = 1
        p0_land_bought = 0
        p1_land_bought = 0
        p0_market_sales = Counter()
        p1_market_sales = Counter()
        
        for t, step in enumerate(steps):
            # Step actions
            a0 = step[0].get('action', [])
            a1 = step[1].get('action', [])
            if t <= 50:
                p0_actions_0_50.append(str(a0))
                p1_actions_0_50.append(str(a1))
            
            # Parse actions
            for act in (a0 if isinstance(a0, list) else [a0]):
                if isinstance(act, dict):
                    atype = act.get('action')
                    if atype == 'buy_animal':
                        p0_animals[act.get('type')] += 1
                    elif atype == 'plant':
                        p0_crops[act.get('crop')] += 1
                    elif atype == 'hire_worker':
                        p0_workers_max += 1
                    elif atype == 'buy_land':
                        p0_land_bought += 1
                    elif atype == 'sell':
                        p0_market_sales[act.get('item')] += act.get('quantity', 1)
                        
            for act in (a1 if isinstance(a1, list) else [a1]):
                if isinstance(act, dict):
                    atype = act.get('action')
                    if atype == 'buy_animal':
                        p1_animals[act.get('type')] += 1
                    elif atype == 'plant':
                        p1_crops[act.get('crop')] += 1
                    elif atype == 'hire_worker':
                        p1_workers_max += 1
                    elif atype == 'buy_land':
                        p1_land_bought += 1
                    elif atype == 'sell':
                        p1_market_sales[act.get('item')] += act.get('quantity', 1)
        
        replay_data.append({
            'file': os.path.basename(rpath),
            'steps': len(steps),
            'p0_reward': r0,
            'p1_reward': r1,
            'p0_actions_0_50': p0_actions_0_50,
            'p1_actions_0_50': p1_actions_0_50,
            'p0_animals': dict(p0_animals),
            'p1_animals': dict(p1_animals),
            'p0_crops': dict(p0_crops),
            'p1_crops': dict(p1_crops),
            'p0_workers': p0_workers_max,
            'p1_workers': p1_workers_max,
            'p0_land': p0_land_bought,
            'p1_land': p1_land_bought,
            'p0_sales': dict(p0_market_sales),
            'p1_sales': dict(p1_market_sales)
        })
    except Exception as e:
        print(f"Error parsing {rpath}: {e}")

print(f"\nSuccessfully parsed {len(replay_data)} replays.")

# Analyze rewards and archetype distribution
print("\n=== REPLAY REWARDS & STRATEGY SUMMARY ===")
for r in replay_data[:10]:
    print(f"File: {r['file'][:30]} | P0: ${r['p0_reward']:,.0f} (Animals: {r['p0_animals']}, Crops: {r['p0_crops']}) | P1: ${r['p1_reward']:,.0f} (Animals: {r['p1_animals']}, Crops: {r['p1_crops']})")

# Check action determinism across turns 0-50
p0_traces = [tuple(r['p0_actions_0_50']) for r in replay_data if len(r['p0_actions_0_50']) >= 50]
p1_traces = [tuple(r['p1_actions_0_50']) for r in replay_data if len(r['p1_actions_0_50']) >= 50]

p0_trace_counts = Counter(p0_traces)
p1_trace_counts = Counter(p1_traces)

print(f"\n=== DETERMINISM OF TURNS 0-50 ===")
print(f"Total P0 traces (>=50 turns): {len(p0_traces)}, Unique opening action sequences: {len(p0_trace_counts)}")
for trace, count in p0_trace_counts.most_common(5):
    print(f"  P0 Pattern repeated {count} times ({count/len(p0_traces)*100:.1f}%)")

print(f"Total P1 traces (>=50 turns): {len(p1_traces)}, Unique opening action sequences: {len(p1_trace_counts)}")
for trace, count in p1_trace_counts.most_common(5):
    print(f"  P1 Pattern repeated {count} times ({count/len(p1_traces)*100:.1f}%)")
