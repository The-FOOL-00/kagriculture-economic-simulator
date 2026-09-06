import json
import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_files = glob.glob('scratch/replays/*.json')
print(f"Analyzing {len(replay_files)} replays...\n")

results = []

for rf in sorted(replay_files):
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
        
    info = data.get('info', {})
    rewards = data.get('rewards', [0, 0])
    team_names = info.get('TeamNames', ['P0', 'P1'])
    
    for p_idx in [0, 1]:
        p_name = team_names[p_idx] if p_idx < len(team_names) else f"P{p_idx}"
        p_reward = rewards[p_idx] if p_idx < len(rewards) else 0
        
        q_steps = {}
        wheat_bought = 0
        milk_sold = 0
        cows_max = 0
        
        for s_idx in range(len(steps)):
            p_data = steps[s_idx][p_idx]
            obs = p_data.get('observation', {})
            farm = obs.get('farms', [{}, {}])[p_idx] if 'farms' in obs else {}
            quads = farm.get('unlocked_quadrants', [])
            
            if len(quads) not in q_steps:
                q_steps[len(quads)] = s_idx
                
            cows = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
            cows_max = max(cows_max, cows)
            
            act = p_data.get('action', {})
            if isinstance(act, dict):
                for ma in act.get('market', []):
                    if isinstance(ma, list) and len(ma) >= 3:
                        if ma[0] == 'BUY_PRODUCT' and ma[1] == 'WHEAT':
                            wheat_bought += int(ma[2])
                        elif ma[0] == 'SELL' and ma[1] == 'MILK':
                            milk_sold += int(ma[2])
                            
        results.append({
            'file': os.path.basename(rf),
            'player': p_name,
            'reward': p_reward,
            'q2_step': q_steps.get(2, -1),
            'q3_step': q_steps.get(3, -1),
            'cows_max': cows_max,
            'wheat_bought': wheat_bought,
            'milk_sold': milk_sold
        })

# Sort by reward descending
results.sort(key=lambda x: x['reward'], reverse=True)

print(f"{'Player / Team':<22} | {'Reward':>8} | {'Q2 Step':>7} | {'Q3 Step':>7} | {'Cows':>4} | {'WheatBought':>11} | {'MilkSold':>8} | Replay File")
print("-" * 110)
for r in results[:25]:
    print(f"{r['player']:<22} | {r['reward']:8.1f} | {r['q2_step']:7d} | {r['q3_step']:7d} | {r['cows_max']:4d} | {r['wheat_bought']:11d} | {r['milk_sold']:8d} | {r['file']}")
