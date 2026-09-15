import json

filepath = "replays/live_tournament/episode_107543042.json"
with open(filepath) as f:
    ep = json.load(f)

print("=== DEEP EXTRACTION: ORIGINATORS (EPISODE 107543042) ===")

# In this replay, ORiginators was Seat 1
opp_seat = 1

tomato_events = []
carrot_events = []
strawberry_events = []

for step, s in enumerate(ep['steps']):
    day = step // 24
    hour = step % 24
    act = s[opp_seat].get('action', {})
    if not act:
        continue
        
    # Market actions
    for m in act.get('market', []):
        if not m: continue
        op = m[0]
        if 'TOMATO' in m:
            tomato_events.append((step, day, hour, 'MARKET', m))
        if 'CARROT' in m:
            carrot_events.append((step, day, hour, 'MARKET', m))
            
    # Unit actions
    units = [act.get('farmer', [])] + act.get('hands', [])
    for u_idx, u in enumerate(units):
        if not u: continue
        op = u[0]
        if op in ['PLANT', 'HARVEST', 'WATER']:
            if len(u) > 1 and u[1] == 'TOMATO':
                tomato_events.append((step, day, hour, f'U{u_idx}_{op}', u))
            elif len(u) > 1 and u[1] == 'CARROT':
                carrot_events.append((step, day, hour, f'U{u_idx}_{op}', u))

print(f"\nTomato Events ({len(tomato_events)} total):")
for e in tomato_events[:30]:
    print(f"Step {e[0]:3d} (Day {e[1]:2d}, Hr {e[2]:2d}): {e[3]} -> {e[4]}")

print(f"\nCarrot Events ({len(carrot_events)} total):")
for e in carrot_events[:30]:
    print(f"Step {e[0]:3d} (Day {e[1]:2d}, Hr {e[2]:2d}): {e[3]} -> {e[4]}")
