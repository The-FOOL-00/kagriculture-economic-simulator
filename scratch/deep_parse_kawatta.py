import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ep_files = [
    ("Episode 104802423 (KawattaTaido #1)", "scratch/replays/V2_Loss_vs_KawattaTaido_104802423.json"),
    ("Episode 104817623 (KawattaTaido #2)", "scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json")
]

for title, fpath in ep_files:
    print("\n" + "=" * 90)
    print(f"DEEP TICK-BY-TICK AUDIT: {title}")
    print("=" * 90)
    
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps", [])
    print(f"Total Steps: {len(steps)}")
    
    # Identify player indices: Player 0 vs Player 1
    # Check team names from first step or metadata if available
    r0_final = steps[-1][0].get("reward", 0)
    r1_final = steps[-1][1].get("reward", 0)
    print(f"Final Rewards: Player 0 = ${r0_final:,.0f} | Player 1 = ${r1_final:,.0f}")
    
    # In these files, Player 0 is KawattaTaido and Player 1 is V2 (or vice versa)
    # Let's inspect step 0 observation to identify farm features
    
    # Track day-by-day stats
    day_rows = []
    
    # Track cumulative market sales by product over time
    p0_market_history = []
    p1_market_history = []
    
    # Track price history for key goods: WOOL, FERTILIZER, WHEAT, MILK, STRAWBERRY, MELON
    price_history = []
    
    for step_idx, step in enumerate(steps):
        day = step_idx // 24
        hour = step_idx % 24
        
        obs0 = step[0].get("observation", {})
        farms = obs0.get("farms", [{}, {}])
        f0 = farms[0] if len(farms) > 0 else {}
        f1 = farms[1] if len(farms) > 1 else {}
        
        market_obs = obs0.get("market", {})
        
        # Track orders at this step
        for p_idx, s in enumerate(step):
            act = s.get("action", {}) or {}
            m_orders = act.get("market", []) or []
            for order in m_orders:
                if isinstance(order, list) and len(order) >= 2:
                    op, item = order[0], order[1]
                    qty = int(order[2]) if len(order) >= 3 else 1
                    entry = {'step': step_idx, 'day': day, 'hour': hour, 'op': op, 'item': item, 'qty': qty}
                    if p_idx == 0:
                        p0_market_history.append(entry)
                    else:
                        p1_market_history.append(entry)
                        
        if hour == 23 or step_idx == len(steps) - 1:
            # End of day snapshot
            # Animals count
            f0_animals = f0.get("animals", {})
            f1_animals = f1.get("animals", {})
            f0_sheep = f0_animals.get("SHEEP", 0) if isinstance(f0_animals, dict) else len([a for a in f0.get("pastures", []) if a.get("type") == "SHEEP"])
            f1_sheep = f1_animals.get("SHEEP", 0) if isinstance(f1_animals, dict) else len([a for a in f1.get("pastures", []) if a.get("type") == "SHEEP"])
            
            # Quads
            f0_quads = len(f0.get("unlocked_quadrants", ["NW"]))
            f1_quads = len(f1.get("unlocked_quadrants", ["NW"]))
            
            # Hands
            f0_hands = len(f0.get("hands", []))
            f1_hands = len(f1.get("hands", []))
            
            # Money
            f0_money = f0.get("money", 0)
            f1_money = f1.get("money", 0)
            
            # Inventory
            f0_inv = f0.get("inventory", {})
            f1_inv = f1.get("inventory", {})
            
            # Market prices
            prices = market_obs.get("prices", {}) if isinstance(market_obs, dict) else {}
            
            day_rows.append({
                'day': day,
                'p0_money': f0_money,
                'p1_money': f1_money,
                'p0_hands': f0_hands,
                'p1_hands': f1_hands,
                'p0_quads': f0_quads,
                'p1_quads': f1_quads,
                'wool_price': prices.get("WOOL", 0),
                'fert_price': prices.get("FERTILIZER", 0),
                'wheat_price': prices.get("WHEAT", 0),
                'milk_price': prices.get("MILK", 0),
                'straw_price': prices.get("STRAWBERRY", 0),
                'melon_price': prices.get("MELON", 0),
                'p0_animals': str(f0.get("animals", f0.get("structures", {}))),
                'p1_animals': str(f1.get("animals", f1.get("structures", {}))),
                'p0_inv_wool': f0_inv.get("WOOL", 0),
                'p1_inv_wool': f1_inv.get("WOOL", 0),
            })
            
    df_days = pd.DataFrame(day_rows)
    print("\n--- Day-by-Day Financial & Asset Progression ---")
    cols = ['day', 'p0_money', 'p1_money', 'p0_hands', 'p1_hands', 'p0_quads', 'p1_quads', 'wool_price', 'fert_price', 'wheat_price', 'milk_price', 'straw_price']
    print(df_days[cols].iloc[[0, 1, 2, 3, 4, 5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 29]].to_string(index=False))
    
    # Analyze market sell volume timeline
    df_p0_m = pd.DataFrame(p0_market_history)
    df_p1_m = pd.DataFrame(p1_market_history)
    
    print("\n--- P0 (KawattaTaido) Market Sells by Product ---")
    if not df_p0_m.empty:
        p0_sells = df_p0_m[df_p0_m['op'] == 'SELL'].groupby('item')['qty'].sum()
        print(p0_sells)
        print("\nP0 Sells by Day (Top Sells):")
        p0_daily_sells = df_p0_m[df_p0_m['op'] == 'SELL'].groupby(['day', 'item'])['qty'].sum().unstack(fill_value=0)
        print(p0_daily_sells[['WOOL', 'FERTILIZER', 'WHEAT', 'MELON', 'STRAWBERRY']].dropna(how='all'))
        
    print("\n--- P1 (V2) Market Sells by Product ---")
    if not df_p1_m.empty:
        p1_sells = df_p1_m[df_p1_m['op'] == 'SELL'].groupby('item')['qty'].sum()
        print(p1_sells)
        print("\nP1 Sells by Day (Top Sells):")
        p1_daily_sells = df_p1_m[df_p1_m['op'] == 'SELL'].groupby(['day', 'item'])['qty'].sum().unstack(fill_value=0)
        print(p1_daily_sells[['WOOL', 'FERTILIZER', 'WHEAT', 'MELON', 'STRAWBERRY', 'MILK']].dropna(how='all'))

