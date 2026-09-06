import os
import sys
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect Crop Dusta, Yuan800, Whyme Labs, KawattaTaido, and Aethel V2 in detail

def analyze_game_deep(fpath, p_idx, team_name):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = data.get("steps", [])
    
    # Financial trajectory
    day_snapshots = []
    
    # Purchases log: seeds, animals, land, workers
    buys_log = []
    sells_log = []
    
    # Tile & building state
    for s_idx, step in enumerate(steps):
        day = s_idx // 24
        hour = s_idx % 24
        obs = step[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        f = farms[p_idx] if len(farms) > p_idx else {}
        
        act = step[p_idx].get("action", {}) or {}
        m_orders = act.get("market", []) or []
        farmer_act = act.get("farmer", []) or []
        hands_act = act.get("hands", []) or []
        
        # Track market buys and sells
        for o in m_orders:
            if isinstance(o, list) and len(o) >= 2:
                op = o[0]
                item = o[1]
                qty = int(o[2]) if len(o) >= 3 else 1
                if op.startswith("BUY"):
                    buys_log.append({'step': s_idx, 'day': day, 'hour': hour, 'op': op, 'item': item, 'qty': qty})
                elif op == "SELL":
                    sells_log.append({'step': s_idx, 'day': day, 'hour': hour, 'op': op, 'item': item, 'qty': qty})
                    
        # Track worker hiring
        for o in m_orders:
            if isinstance(o, list) and len(o) >= 1 and o[0] == "HIRE":
                buys_log.append({'step': s_idx, 'day': day, 'hour': hour, 'op': 'HIRE', 'item': 'WORKER', 'qty': 1})
                
        if hour == 23 or s_idx == len(steps) - 1:
            tiles = f.get("tiles", [])
            cows = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
            sheep = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
            geese = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "GOOSE")
            pastures = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
            
            # Crops breakdown
            crops = {}
            for row in tiles:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        c_name = t.get("crop", "UNKNOWN")
                        crops[c_name] = crops.get(c_name, 0) + 1
                        
            quads = len(f.get("unlocked_quadrants", []))
            hands = len(f.get("hands", []))
            money = f.get("money", 0)
            
            # Town shops
            town = obs.get("town", {})
            shops = town.get("unlocked_shops", [])
            
            day_snapshots.append({
                'day': day,
                'money': money,
                'hands': hands,
                'quads': quads,
                'cows': cows,
                'sheep': sheep,
                'geese': geese,
                'pastures': pastures,
                'crops': crops,
                'shops': list(shops)
            })
            
    df_snaps = pd.DataFrame(day_snapshots)
    df_buys = pd.DataFrame(buys_log)
    df_sells = pd.DataFrame(sells_log)
    
    final_reward = steps[-1][p_idx].get("reward", 0)
    opp_reward = steps[-1][1 - p_idx].get("reward", 0)
    
    return {
        'team': team_name,
        'file': os.path.basename(fpath),
        'reward': final_reward,
        'opp_reward': opp_reward,
        'margin': final_reward - opp_reward,
        'snaps': df_snaps,
        'buys': df_buys,
        'sells': df_sells
    }

print("=" * 90)
print("2. DEEP FORENSIC DISSECTION OF TOP-10 AGENTS & KAWATTATAIDO")
print("=" * 90)

# Analyze key episodes
cases = [
    ("scratch/replays/Crop_Dusta_104824599.json", 1, "Crop_Dusta (#2)"),
    ("scratch/replays/Crop_Dusta_104821339.json", 0, "Crop_Dusta (#2 - Game 2)"),
    ("scratch/replays/Yuan800_104824200.json", 0, "Yuan800 (#3)"),
    ("scratch/replays/Whyme_Labs_104824599.json", 0, "Whyme_Labs (#5)"),
    ("scratch/replays/MtN_104824200.json", 1, "MtN (#1)"),
    ("scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json", 0, "KawattaTaido (Live Flooder)"),
    ("scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json", 1, "Aethel_V2 (Live Match)"),
]

reports = []
for fpath, p_idx, name in cases:
    if os.path.exists(fpath):
        res = analyze_game_deep(fpath, p_idx, name)
        reports.append(res)
        
for r in reports:
    print("\n" + "=" * 80)
    print(f"AGENT PROFILE: {r['team']} | Episode: {r['file']}")
    print(f"Final Score: ${r['reward']:,.1f} vs Opponent: ${r['opp_reward']:,.1f} (Margin: ${r['margin']:+,.1f})")
    print("=" * 80)
    
    snaps = r['snaps']
    # Print key days: 1, 3, 5, 7, 10, 15, 20, 25, 29
    key_days = [0, 2, 4, 6, 9, 14, 19, 24, 29]
    cols = ['day', 'money', 'hands', 'quads', 'cows', 'sheep', 'pastures']
    print(snaps.loc[snaps['day'].isin([d for d in [0, 2, 4, 6, 9, 14, 19, 24, 29] if d < len(snaps)]), cols].to_string(index=False))
    
    print("\nCrop Allocation Timeline:")
    for idx, row in snaps.iterrows():
        if row['day'] in [1, 3, 5, 8, 12, 16, 20, 25, 29]:
            print(f"  Day {row['day']:2d}: Crops = {row['crops']} | Unlocked Shops = {row['shops']}")
            
    print("\nTotal Market Sells Summary:")
    if not r['sells'].empty:
        s_grp = r['sells'].groupby('item')['qty'].sum()
        print(s_grp.to_dict())
        
    print("\nTotal Purchases Summary:")
    if not r['buys'].empty:
        b_grp = r['buys'].groupby(['op', 'item'])['qty'].sum()
        print(b_grp.to_dict())
        
