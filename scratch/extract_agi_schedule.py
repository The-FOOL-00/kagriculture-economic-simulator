import json

filepath = "replays/live_tournament/episode_107560807.json"
with open(filepath) as f:
    ep = json.load(f)

print("=== DEEP EXTRACTION: AGI (EPISODE 107560807) ===")
opp_seat = 1

carrot_events = []
for step, s in enumerate(ep['steps']):
    day = step // 24
    hour = step % 24
    act = s[opp_seat].get('action', {})
    if not act: continue
    
    # Market
    for m in act.get('market', []):
        if m and 'CARROT' in m:
            carrot_events.append((step, day, hour, 'MARKET', m))
            
    # Units
    units = [act.get('farmer', [])] + act.get('hands', [])
    for u_idx, u in enumerate(units):
        if not u: continue
        op = u[0]
        if op in ['PLANT', 'HARVEST'] and len(u) > 1 and u[1] == 'CARROT':
            carrot_events.append((step, day, hour, f'U{u_idx}_{op}', u))

print(f"Total Carrot Events: {len(carrot_events)}")
for e in carrot_events[:40]:
    print(f"Step {e[0]:3d} (Day {e[1]:2d}, Hr {e[2]:2d}): {e[3]} -> {e[4]}")
