import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

top_ep_files = [
    ("MtN (Rank 1) vs Yuan800 (Rank 3)", "scratch/replays/top_episodes_top_55947871_104824200.json"),
    ("Crop Dusta (Rank 2) vs Whyme Labs (Rank 5)", "scratch/replays/top_episodes_top_55929317_104824599.json"),
    ("3정훈 (Rank 4)", "scratch/replays/top_episodes_top_55944801_104823350.json"),
]

for title, fpath in top_ep_files:
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
    print("\n" + "=" * 90)
    print(f"TOP-10 MATCH FORENSIC AUDIT: {title} ({os.path.basename(fpath)})")
    print("=" * 90)
    
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps", [])
    r0_final = steps[-1][0].get("reward", 0)
    r1_final = steps[-1][1].get("reward", 0)
    print(f"Final Rewards: Player 0 = ${r0_final:,.0f} | Player 1 = ${r1_final:,.0f}")
    
    day_rows = []
    p0_m = []
    p1_m = []
    
    for step_idx, step in enumerate(steps):
        day = step_idx // 24
        hour = step_idx % 24
        
        obs0 = step[0].get("observation", {})
        farms = obs0.get("farms", [{}, {}])
        f0 = farms[0] if len(farms) > 0 else {}
        f1 = farms[1] if len(farms) > 1 else {}
        
        market_obs = obs0.get("market", {})
        prices = market_obs.get("prices", {}) if isinstance(market_obs, dict) else {}
        
        for p_idx, s in enumerate(step):
            act = s.get("action", {}) or {}
            for order in act.get("market", []) or []:
                if isinstance(order, list) and len(order) >= 2:
                    op, item = order[0], order[1]
                    qty = int(order[2]) if len(order) >= 3 else 1
                    e = {'step': step_idx, 'day': day, 'hour': hour, 'op': op, 'item': item, 'qty': qty}
                    if p_idx == 0:
                        p0_m.append(e)
                    else:
                        p1_m.append(e)
                        
        if hour == 23 or step_idx == len(steps) - 1:
            day_rows.append({
                'day': day,
                'p0_money': f0.get("money", 0),
                'p1_money': f1.get("money", 0),
                'p0_hands': len(f0.get("hands", [])),
                'p1_hands': len(f1.get("hands", [])),
                'p0_quads': len(f0.get("unlocked_quadrants", ["NW"])),
                'p1_quads': len(f1.get("unlocked_quadrants", ["NW"])),
                'wheat_price': prices.get("WHEAT", 0),
                'wool_price': prices.get("WOOL", 0),
                'milk_price': prices.get("MILK", 0),
                'straw_price': prices.get("STRAWBERRY", 0),
                'melon_price': prices.get("MELON", 0),
                'fert_price': prices.get("FERTILIZER", 0),
            })
            
    df_days = pd.DataFrame(day_rows)
    cols = ['day', 'p0_money', 'p1_money', 'p0_hands', 'p1_hands', 'p0_quads', 'p1_quads', 'wheat_price', 'wool_price', 'milk_price', 'straw_price', 'fert_price']
    print(df_days[cols].iloc[[0, 1, 2, 3, 4, 5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 29]].to_string(index=False))
    
    df_p0 = pd.DataFrame(p0_m)
    df_p1 = pd.DataFrame(p1_m)
    
    print("\nPlayer 0 Sells by Item:")
    if not df_p0.empty:
        print(df_p0[df_p0['op'] == 'SELL'].groupby('item')['qty'].sum())
    print("\nPlayer 1 Sells by Item:")
    if not df_p1.empty:
        print(df_p1[df_p1['op'] == 'SELL'].groupby('item')['qty'].sum())

