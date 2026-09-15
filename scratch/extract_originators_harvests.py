import json

with open("replays/live_tournament/episode_107543042.json") as f:
    ep = json.load(f)

opp_seat = 1

harvest_events = []
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
            harvest_events.append((step, day, hour, u_idx, tuple(pos) if pos else None))

print(f"Total Harvest Events for ORiginators: {len(harvest_events)}")
harvests_by_day = {}
for h in harvest_events:
    day = h[1]
    harvests_by_day[day] = harvests_by_day.get(day, 0) + 1
for d in sorted(harvests_by_day.keys()):
    print(f"Day {d:2d}: {harvests_by_day[d]:2d} harvests")
