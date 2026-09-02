import os
import sys
import json
import glob
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

top_files = glob.glob("scratch/replays/top_*.json")
print(f"Top team replay files: {top_files}")

for fpath in top_files:
    print("\n" + "="*90)
    print(f"ANALYZING TOP TEAM MATCH: {os.path.basename(fpath)}")
    print("="*90)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = data.get("steps", [])
    if not steps:
        continue
    final_step = steps[-1]
    
    # Get metadata
    r0 = final_step[0].get("reward", 0)
    r1 = final_step[1].get("reward", 0)
    
    print(f"Final Score: Player 0: ${r0:,.0f} | Player 1: ${r1:,.0f}")
    
    # Analyze both players in detail
    for p_idx in [0, 1]:
        plants = {}
        sells = {}
        buys = {}
        hands_count = 0
        quads = []
        animals = {}
        town_orders_count = 0
        
        # Track timeline of events
        timeline = []
        
        for step_idx, step in enumerate(steps):
            day = step_idx // 24
            hour = step_idx % 24
            
            obs = step[p_idx].get("observation", {})
            farms = obs.get("farms", [{}, {}])
            f = farms[p_idx] if len(farms) > p_idx else {}
            
            hands = f.get("hands", [])
            hands_count = max(hands_count, len(hands))
            quads = f.get("unlocked_quadrants", ["NW"])
            
            act = step[p_idx].get("action", {}) or {}
            
            # Farmer action
            farmer_act = act.get("farmer", []) or []
            hands_acts = act.get("hands", []) or []
            
            for u in [farmer_act] + hands_acts:
                if isinstance(u, list) and len(u) >= 2:
                    if u[0] == "PLANT":
                        plants[u[1]] = plants.get(u[1], 0) + 1
                    elif u[0] == "BUY":
                        buys[u[1]] = buys.get(u[1], 0) + 1
                        
            # Market actions
            for m in act.get("market", []) or []:
                if isinstance(m, list) and len(m) >= 2:
                    op = m[0]
                    item = m[1]
                    qty = int(m[2]) if len(m) >= 3 else 1
                    if op == "SELL":
                        sells[item] = sells.get(item, 0) + qty
                    elif op == "BUY":
                        buys[item] = buys.get(item, 0) + qty
                        
            # Track daily progression at 23:00
            if hour == 23:
                money = f.get("money", 0)
                timeline.append({
                    'day': day,
                    'money': money,
                    'hands': len(hands),
                    'quads': len(quads)
                })
                
        print(f"\n--- Player {p_idx} Profile ---")
        print(f"Max Hands: {hands_count}, Quads: {len(quads)} ({quads})")
        print(f"Crops Planted: {plants}")
        print(f"Items Bought: {buys}")
        print(f"Items Sold to Market: {sells}")
        print("Daily Money Progression:")
        for t in timeline:
            if t['day'] in [0, 1, 2, 3, 5, 7, 10, 12, 15, 18, 20, 23, 25, 27, 29]:
                print(f"  Day {t['day']:2d}: ${t['money']:10,.0f} | Hands: {t['hands']} | Quads: {t['quads']}")

