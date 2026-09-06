import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
p_idx = 1 # Crop Dusta

print("=== MARKET TRADES ON DAYS 10 TO 16 (Steps 240 to 400) ===")

for s in range(240, 400):
    obs = steps[s][p_idx]['observation']
    farm = obs['farms'][p_idx]
    shed = obs['private']['shed']
    m_prices = obs['market']['prices']
    money = farm['money']
    
    act = steps[s][p_idx].get('action', {})
    m_act = act.get('market', []) if isinstance(act, dict) else []
    
    if m_act:
        print(f"[Step {s:3d} | D{s//24:02d}:H{s%24:02d}] Cash: ${money:7.1f} | Prices: Wheat=${m_prices.get('WHEAT', 0)}, Milk=${m_prices.get('MILK', 0)}, Straw=${m_prices.get('STRAWBERRY', 0)}, Tomato=${m_prices.get('TOMATO', 0)} | Shed: {shed}")
        for ma in m_act:
            print(f"    ACTION: {ma}")
