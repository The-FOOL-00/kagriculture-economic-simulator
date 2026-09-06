import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_dir = 'scratch/replays'
files = [f for f in os.listdir(replay_dir) if f.endswith('.json') and os.path.getsize(os.path.join(replay_dir, f)) > 1000]

print(f"Found {len(files)} replays to cross-check across top meta agents.\n")

meta_summary = []

for fn in sorted(files):
    fp = os.path.join(replay_dir, fn)
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        continue
        
    info = data.get('info', {})
    team_names = info.get('TeamNames', ['P0', 'P1'])
    rewards = data.get('rewards', [0, 0])
    steps = data.get('steps', [])
    
    if len(steps) < 100:
        continue
        
    for p_idx in [0, 1]:
        p_name = team_names[p_idx] if len(team_names) > p_idx else f"P{p_idx}"
        rew = rewards[p_idx] if len(rewards) > p_idx else 0
        
        # We are interested in Top Meta agents: Whyme Labs, Yuan800, MtN, Kawatta, Crop Dusta, 3JungHoon, Aethel/V2
        # Let's extract key telemetry
        q2_step = None
        q3_step = None
        max_pastures = 0
        max_cows = 0
        max_sheep = 0
        max_workers = 0
        total_wheat_bought = 0
        total_wheat_sold = 0
        total_milk_sold = 0
        total_wool_sold = 0
        total_crops_sold = {}
        
        for s_idx, s in enumerate(steps):
            p_data = s[p_idx]
            obs = p_data.get('observation', {})
            farms = obs.get('farms', [])
            farm = farms[p_idx] if len(farms) > p_idx else {}
            quads = farm.get('unlocked_quadrants', [])
            
            if q2_step is None and len(quads) >= 2:
                q2_step = s_idx
            if q3_step is None and len(quads) >= 3:
                q3_step = s_idx
                
            pastures = 0
            cows = 0
            sheep = 0
            for row in farm.get('tiles', []):
                for t in row:
                    if isinstance(t, dict):
                        if t.get('kind') == 'PASTURE':
                            pastures += 1
                        a = t.get('animal')
                        if a == 'COW':
                            cows += 1
                        elif a == 'SHEEP':
                            sheep += 1
            max_pastures = max(max_pastures, pastures)
            max_cows = max(max_cows, cows)
            max_sheep = max(max_sheep, sheep)
            
            w_cnt = len(farm.get('hands', [])) + (1 if farm.get('farmer') else 0)
            max_workers = max(max_workers, w_cnt)
            
            act = p_data.get('action', {})
            m_act = act.get('market', []) if isinstance(act, dict) else []
            for ma in m_act:
                if isinstance(ma, list) and len(ma) >= 3:
                    op, item, qty = ma[0], ma[1], int(ma[2])
                    if op == 'BUY_PRODUCT' and item == 'WHEAT':
                        total_wheat_bought += qty
                    elif op in ['SELL_PRODUCT', 'SELL']:
                        if item == 'WHEAT':
                            total_wheat_sold += qty
                        elif item == 'MILK':
                            total_milk_sold += qty
                        elif item == 'WOOL':
                            total_wool_sold += qty
                        else:
                            total_crops_sold[item] = total_crops_sold.get(item, 0) + qty
                            
        meta_summary.append({
            'file': fn,
            'player': p_name,
            'p_idx': p_idx,
            'reward': rew,
            'q2_step': q2_step,
            'q3_step': q3_step,
            'max_pastures': max_pastures,
            'max_cows': max_cows,
            'max_sheep': max_sheep,
            'max_workers': max_workers,
            'wheat_bought': total_wheat_bought,
            'wheat_sold': total_wheat_sold,
            'milk_sold': total_milk_sold,
            'wool_sold': total_wool_sold,
            'crops_sold': total_crops_sold
        })

# Sort by reward descending
meta_summary.sort(key=lambda x: x['reward'], reverse=True)

print(f"{'Player':<20} | {'Reward':>8} | {'Q2':>4} | {'Q3':>4} | {'Past':>4} | {'Cows':>4} | {'Shp':>3} | {'W':>2} | {'W_Buy':>5} | {'W_Sell':>6} | {'Milk':>4} | {'Wool':>4} | {'Top Crops Sold'}")
print("-" * 120)

for row in meta_summary[:35]:
    crops_s = ", ".join([f"{k}:{v}" for k, v in sorted(row['crops_sold'].items(), key=lambda x: -x[1])[:3]])
    q2_s = f"{row['q2_step']}" if row['q2_step'] is not None else "-"
    q3_s = f"{row['q3_step']}" if row['q3_step'] is not None else "-"
    print(f"{row['player']:<20} | ${row['reward']:7.0f} | {q2_s:>4} | {q3_s:>4} | {row['max_pastures']:4d} | {row['max_cows']:4d} | {row['max_sheep']:3d} | {row['max_workers']:2d} | {row['wheat_bought']:5d} | {row['wheat_sold']:6d} | {row['milk_sold']:4d} | {row['wool_sold']:4d} | {crops_s}")

with open('scratch/meta_top_agents_crosscheck.json', 'w') as f:
    json.dump(meta_summary, f, indent=2)
