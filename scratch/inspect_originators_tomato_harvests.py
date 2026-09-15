import json

filepath = "replays/live_tournament/episode_107543042.json"
with open(filepath) as f:
    ep = json.load(f)

opp_seat = 1

tomato_harvests = []
for step, s in enumerate(ep['steps']):
    day = step // 24
    hour = step % 24
    opp_data = s[opp_seat]
    act = opp_data.get('action', {})
    if not act: continue
    
    farmer_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('farmer')
    hands_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('hands', [])
    all_pos = [farmer_pos] + hands_pos if farmer_pos else []
    
    units = [act.get('farmer', [])] + act.get('hands', [])
    for u_idx, u in enumerate(units):
        if not u: continue
        if u[0] == 'HARVEST':
            pos = all_pos[u_idx] if u_idx < len(all_pos) else None
            # Check what crop was at pos in farm tiles
            tiles = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('tiles', [])
            if pos and 0 <= pos[1] < len(tiles) and 0 <= pos[0] < len(tiles[0]):
                t = tiles[pos[1]][pos[0]]
                if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                    tomato_harvests.append((step, day, hour, u_idx, pos, t.get('yield_units')))

print(f"Total Tomato Harvests for ORiginators: {len(tomato_harvests)}")
harvests_by_day = {}
for h in tomato_harvests:
    d = h[1]
    harvests_by_day[d] = harvests_by_day.get(d, 0) + 1
for d in sorted(harvests_by_day.keys()):
    print(f"Day {d:2d}: {harvests_by_day[d]:2d} tomato harvests")
