import os
import sys
import json
import glob
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 90)
print("DEEP REPLAY FORENSICS: V2 LOSSES, V2 WINS, & TOP-10 LEADERBOARD CHAMPIONS")
print("=" * 90)

replay_files = glob.glob("scratch/replays/*.json")
# Filter out non-replay or tiny files
valid_replays = [f for f in replay_files if os.path.getsize(f) > 100000]
print(f"Found {len(valid_replays)} valid replay files to analyze:")
for f in valid_replays:
    print(f"  - {os.path.basename(f)} ({os.path.getsize(f):,} bytes)")

def parse_full_replay(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps", [])
    if not steps:
        return None
        
    num_steps = len(steps)
    final_step = steps[-1]
    
    r0 = final_step[0].get("reward", 0)
    r1 = final_step[1].get("reward", 0)
    
    # Track actions, economy, and inventory for both players
    p_data = {
        0: {
            'plants': {}, 'market_sells': {}, 'market_buys': {}, 'town_sells': 0,
            'max_hands': 0, 'quads_unlocked': [], 'animals_bought': {},
            'daily_money': [], 'daily_net_worth': [], 'rain_events': 0,
            'livestock_losses': 0, 'food_stock_avg': []
        },
        1: {
            'plants': {}, 'market_sells': {}, 'market_buys': {}, 'town_sells': 0,
            'max_hands': 0, 'quads_unlocked': [], 'animals_bought': {},
            'daily_money': [], 'daily_net_worth': [], 'rain_events': 0,
            'livestock_losses': 0, 'food_stock_avg': []
        }
    }
    
    for step_idx, step in enumerate(steps):
        day = step_idx // 24
        hour = step_idx % 24
        
        obs0 = step[0].get("observation", {})
        farms = obs0.get("farms", [{}, {}])
        
        for p_idx in [0, 1]:
            farm = farms[p_idx] if len(farms) > p_idx else {}
            s_agent = step[p_idx] if len(step) > p_idx else {}
            act = s_agent.get("action", {}) or {}
            
            # Hands count
            hands = farm.get("hands", [])
            p_data[p_idx]['max_hands'] = max(p_data[p_idx]['max_hands'], len(hands))
            
            # Quads
            quads = farm.get("unlocked_quadrants", ["NW"])
            p_data[p_idx]['quads_unlocked'] = quads
            
            # Market actions
            m_orders = act.get("market", []) or []
            for order in m_orders:
                if isinstance(order, list) and len(order) >= 2:
                    op = order[0]
                    item = order[1]
                    qty = int(order[2]) if len(order) >= 3 else 1
                    if op == "SELL":
                        p_data[p_idx]['market_sells'][item] = p_data[p_idx]['market_sells'].get(item, 0) + qty
                    elif op == "BUY":
                        p_data[p_idx]['market_buys'][item] = p_data[p_idx]['market_buys'].get(item, 0) + qty
                        if "COW" in item or "SHEEP" in item or "CHICKEN" in item or "PIG" in item:
                            p_data[p_idx]['animals_bought'][item] = p_data[p_idx]['animals_bought'].get(item, 0) + qty
                            
            # Plant actions
            farmer_act = act.get("farmer", []) or []
            hands_acts = act.get("hands", []) or []
            all_unit_acts = [farmer_act] + hands_acts
            for u_act in all_unit_acts:
                if isinstance(u_act, list) and len(u_act) >= 2 and u_act[0] == "PLANT":
                    crop = u_act[1]
                    p_data[p_idx]['plants'][crop] = p_data[p_idx]['plants'].get(crop, 0) + 1
                    
            if hour == 23 or step_idx == num_steps - 1:
                money = farm.get("money", 0)
                p_data[p_idx]['daily_money'].append(money)
                
    return {
        'file': os.path.basename(file_path),
        'num_steps': num_steps,
        'r0': r0,
        'r1': r1,
        'p0': p_data[0],
        'p1': p_data[1]
    }

results = []
for f in valid_replays:
    parsed = parse_full_replay(f)
    if parsed:
        results.append(parsed)

print(f"\nSuccessfully parsed {len(results)} matches.")

for res in results:
    fname = res['file']
    print("\n" + "-"*85)
    print(f"MATCH: {fname}")
    print(f"Player 0: ${res['r0']:,.0f} | Player 1: ${res['r1']:,.0f} | Margin (P0 - P1): ${res['r0'] - res['r1']:+,.0f}")
    
    p0 = res['p0']
    p1 = res['p1']
    
    print(f"P0 Animals Bought: {p0['animals_bought']} | Max Hands: {p0['max_hands']} | Quads: {len(p0['quads_unlocked'])}")
    print(f"P0 Crops Planted: {p0['plants']}")
    print(f"P0 Market Sells: {p0['market_sells']}")
    print(f"P0 Key Days Money [D2, D5, D10, D15, D20, D25, D29]: {[p0['daily_money'][d] for d in [2, 5, 10, 15, 20, 25, len(p0['daily_money'])-1] if d < len(p0['daily_money'])]}")
    
    print(f"P1 Animals Bought: {p1['animals_bought']} | Max Hands: {p1['max_hands']} | Quads: {len(p1['quads_unlocked'])}")
    print(f"P1 Crops Planted: {p1['plants']}")
    print(f"P1 Market Sells: {p1['market_sells']}")
    print(f"P1 Key Days Money [D2, D5, D10, D15, D20, D25, D29]: {[p1['daily_money'][d] for d in [2, 5, 10, 15, 20, 25, len(p1['daily_money'])-1] if d < len(p1['daily_money'])]}")

with open("scratch/deep_replay_forensics_summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
