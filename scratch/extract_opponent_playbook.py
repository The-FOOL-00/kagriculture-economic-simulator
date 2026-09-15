import json
from collections import defaultdict

episodes_to_analyze = [
    ('episode_107543042.json', 'ORiginators', 1), # (filename, opp_name, opp_seat)
    ('episode_107560807.json', 'AGI', 1),
    ('episode_107563778.json', 'Meteor', 1),
    ('episode_107581148.json', 'Re:dorf', 1),
    ('episode_107564294.json', 'Les 2 oies', 1),
    ('episode_107582150.json', 'xxxxyt', 1),
    ('episode_107522150.json', 'snaykey', 1),
]

for filename, opp_name, opp_seat in episodes_to_analyze:
    filepath = f"replays/live_tournament/{filename}"
    with open(filepath) as f:
        ep = json.load(f)
    
    our_seat = 1 - opp_seat
    final_opp_cash = ep['steps'][719][opp_seat]['reward']
    final_our_cash = ep['steps'][719][our_seat]['reward']
    
    # Analyze actions across 720 steps
    opp_market_sells = defaultdict(int)
    opp_market_buys = defaultdict(int)
    opp_hires = 0
    opp_crops_planted = defaultdict(int)
    opp_animals_placed = defaultdict(int)
    
    our_market_sells = defaultdict(int)
    
    for step_i, step in enumerate(ep['steps']):
        opp_data = step[opp_seat]
        our_data = step[our_seat]
        act = opp_data.get('action')
        if not act:
            continue
        
        # market orders
        for m in act.get('market', []):
            op = m[0]
            if op == 'SELL':
                item, qty = m[1], m[2]
                opp_market_sells[item] += qty
            elif op == 'BUY_PRODUCT':
                item, qty = m[1], m[2]
                opp_market_buys[f"PROD_{item}"] += qty
            elif op == 'BUY_SEED':
                item, qty = m[1], m[2]
                opp_market_buys[f"SEED_{item}"] += qty
            elif op == 'BUY_ANIMAL':
                item, qty = m[1], m[2]
                opp_market_buys[f"ANIMAL_{item}"] += qty
            elif op == 'HIRE':
                opp_hires += 1
                
        # unit actions (farmer + hands)
        unit_ops = [act.get('farmer', [])] + act.get('hands', [])
        for u in unit_ops:
            if not u:
                continue
            op = u[0]
            if op == 'PLANT' and len(u) > 1:
                opp_crops_planted[u[1]] += 1
            elif op == 'PLACE' and len(u) > 1:
                opp_animals_placed[u[1]] += 1
                
        # our sells
        our_act = our_data.get('action')
        if our_act:
            for m in our_act.get('market', []):
                if m[0] == 'SELL':
                    our_market_sells[m[1]] += m[2]

    print("="*70)
    print(f"OPPONENT: {opp_name} ({filename})")
    print(f"Final Cash: Opponent ${final_opp_cash:,.0f} vs Ours ${final_our_cash:,.0f} (Margin: ${final_opp_cash - final_our_cash:+,.0f})")
    print(f"Opponent Total Hires: {opp_hires}")
    print(f"Opponent Crops Planted: {dict(opp_crops_planted)}")
    print(f"Opponent Animals Placed: {dict(opp_animals_placed)}")
    print(f"Opponent Market Buys: {dict(opp_market_buys)}")
    print(f"Opponent Market Sells: {dict(opp_market_sells)}")
    print(f"Our Market Sells:      {dict(our_market_sells)}")
