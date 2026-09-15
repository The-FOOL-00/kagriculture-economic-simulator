import json

for ep_id, name in [("107560807", "AGI"), ("107581148", "Re:dorf")]:
    filepath = f"replays/live_tournament/episode_{ep_id}.json"
    with open(filepath) as f:
        ep = json.load(f)
    print(f"\n=== {name} (Episode {ep_id}) ===")
    opp_seat = 1
    
    carrot_plants = []
    carrot_harvests = []
    cows = 0
    hands_by_day = {}
    
    for step, s in enumerate(ep['steps']):
        day = step // 24
        opp_data = s[opp_seat]
        act = opp_data.get('action', {})
        if not act: continue
        
        farmer_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('farmer')
        hands_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('hands', [])
        all_pos = [farmer_pos] + hands_pos if farmer_pos else []
        hands_by_day[day] = len(hands_pos)
        
        units = [act.get('farmer', [])] + act.get('hands', [])
        for u_idx, u in enumerate(units):
            if not u: continue
            if u[0] == 'PLANT' and len(u) > 1 and u[1] == 'CARROT':
                pos = all_pos[u_idx] if u_idx < len(all_pos) else None
                carrot_plants.append((step, day, pos))
            elif u[0] == 'HARVEST':
                pos = all_pos[u_idx] if u_idx < len(all_pos) else None
                # We can check tile in observation to see if it was carrot
                carrot_harvests.append((step, day, pos))

    print(f"Total Carrot Plant actions: {len(carrot_plants)}")
    print(f"Workers by day: {[hands_by_day[d] for d in range(0, 30, 5)]}")
    if carrot_plants:
        print("First 10 carrot plants:", carrot_plants[:10])
