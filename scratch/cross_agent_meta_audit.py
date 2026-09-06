import json
import glob
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

replay_files = glob.glob('scratch/replays/*.json')
print(f"Total Replay Files Found: {len(replay_files)}")

team_records = {}

for rf in replay_files:
    try:
        with open(rf, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        continue
    if not isinstance(data, dict) or 'steps' not in data:
        continue
        
    steps = data.get('steps', [])
    if len(steps) < 100:
        continue
        
    team_names = data.get('info', {}).get('TeamNames', ['P0', 'P1'])
    rewards = data.get('rewards', [0, 0])
    seed = data.get('info', {}).get('seed', 0)
    
    for p_idx in [0, 1]:
        tname = team_names[p_idx]
        reward = rewards[p_idx] if p_idx < len(rewards) else 0
        
        # Analyze trajectory for p_idx
        q2_step = None
        q3_step = None
        max_cows = 0
        max_sheep = 0
        max_pastures = 0
        max_workers = 0
        wheat_bought = 0
        wheat_cost = 0
        milk_sold = 0
        milk_rev = 0
        wool_sold = 0
        wool_rev = 0
        melon_sold = 0
        straw_sold = 0
        tomato_sold = 0
        carrot_sold = 0
        fert_sold = 0
        
        for s, step_data in enumerate(steps):
            obs = step_data[p_idx].get('observation', {})
            farm = obs.get('farms', [{}, {}])[p_idx] if 'farms' in obs else {}
            quads = len(farm.get('unlocked_quadrants', []))
            if quads >= 2 and q2_step is None:
                q2_step = s
            if quads >= 3 and q3_step is None:
                q3_step = s
                
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
            max_cows = max(max_cows, cows)
            max_sheep = max(max_sheep, sheep)
            max_pastures = max(max_pastures, pastures)
            workers = len(farm.get('hands', [])) + (1 if farm.get('farmer') else 0)
            max_workers = max(max_workers, workers)
            
            act = step_data[p_idx].get('action', {})
            m_acts = act.get('market', []) if isinstance(act, dict) else []
            m_prices = obs.get('market', {}).get('prices', {})
            for ma in m_acts:
                if isinstance(ma, list) and len(ma) >= 3:
                    op, item, qty = ma[0], ma[1], int(ma[2])
                    p = float(m_prices.get(item, 0))
                    if op == 'BUY_PRODUCT' and item == 'WHEAT':
                        wheat_bought += qty
                        wheat_cost += qty * p
                    elif op == 'SELL':
                        if item == 'MILK':
                            milk_sold += qty
                            milk_rev += qty * p
                        elif item == 'WOOL':
                            wool_sold += qty
                            wool_rev += qty * p
                        elif item == 'MELON':
                            melon_sold += qty
                        elif item == 'STRAWBERRY':
                            straw_sold += qty
                        elif item == 'TOMATO':
                            tomato_sold += qty
                        elif item == 'CARROT':
                            carrot_sold += qty
                        elif item == 'FERTILIZER':
                            fert_sold += qty

        # Group into normalized team name
        clean_name = "Unknown"
        for candidate in ["Whyme Labs", "Crop Dusta", "Yuan800", "MtN", "Kawatta", "Aethel"]:
            if candidate.lower() in tname.lower():
                clean_name = candidate
                break
        if clean_name == "Unknown":
            clean_name = tname[:15]
            
        if clean_name not in team_records:
            team_records[clean_name] = []
            
        team_records[clean_name].append({
            'file': os.path.basename(rf),
            'seed': seed,
            'reward': reward,
            'q2_step': q2_step or 720,
            'q3_step': q3_step or 720,
            'max_cows': max_cows,
            'max_sheep': max_sheep,
            'max_pastures': max_pastures,
            'max_workers': max_workers,
            'wheat_bought': wheat_bought,
            'wheat_cost': wheat_cost,
            'milk_sold': milk_sold,
            'wool_sold': wool_sold,
            'melon_sold': melon_sold,
            'straw_sold': straw_sold,
            'fert_sold': fert_sold,
        })

print("\n" + "=" * 140)
print(f"{'Team Name':<15} | {'N':>3} | {'Mean Reward':>12} | {'Q2 Step':>8} | {'Q3 Step':>8} | {'Cows':>5} | {'Sheep':>5} | {'Pastures':>8} | {'WheatBought':>11} | {'MilkSold':>8} | {'Melons':>6} | {'Straw':>6}")
print("-" * 140)

for tname, recs in sorted(team_records.items(), key=lambda x: np.mean([r['reward'] for r in x[1]]), reverse=True):
    n = len(recs)
    rew = np.mean([r['reward'] for r in recs])
    q2 = np.mean([r['q2_step'] for r in recs])
    q3 = np.mean([r['q3_step'] for r in recs])
    cows = np.mean([r['max_cows'] for r in recs])
    sheep = np.mean([r['max_sheep'] for r in recs])
    past = np.mean([r['max_pastures'] for r in recs])
    wb = np.mean([r['wheat_bought'] for r in recs])
    ms = np.mean([r['milk_sold'] for r in recs])
    mel = np.mean([r['melon_sold'] for r in recs])
    straw = np.mean([r['straw_sold'] for r in recs])
    
    print(f"{tname:<15} | {n:3d} | ${rew:11.1f} | {q2:8.1f} | {q3:8.1f} | {cows:5.1f} | {sheep:5.1f} | {past:8.1f} | {wb:11.1f} | {ms:8.1f} | {mel:6.1f} | {straw:6.1f}")

print("=" * 140)
