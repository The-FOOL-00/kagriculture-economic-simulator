import json

with open("replays/live_tournament/episode_107543042.json") as f:
    ep = json.load(f)

print("=== ORIGINATORS TILE COORDINATES ===")
opp_seat = 1 # ORiginators was Seat 1

tomato_tiles = set()
strawberry_tiles = set()
melon_tiles = set()

for step, s in enumerate(ep['steps']):
    day = step // 24
    opp_data = s[opp_seat]
    act = opp_data.get('action', {})
    if not act: continue
    
    # Check positions from farm observation
    farmer_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('farmer')
    hands_pos = opp_data.get('observation', {}).get('farms', [{}, {}])[opp_seat].get('hands', [])
    all_pos = [farmer_pos] + hands_pos if farmer_pos else []
    
    units = [act.get('farmer', [])] + act.get('hands', [])
    for u_idx, u in enumerate(units):
        if not u: continue
        op = u[0]
        if op == 'PLANT' and len(u) > 1:
            crop = u[1]
            pos = all_pos[u_idx] if u_idx < len(all_pos) else None
            if crop == 'TOMATO':
                tomato_tiles.add((step, day, u_idx, tuple(pos) if pos else None))
            elif crop == 'STRAWBERRY':
                strawberry_tiles.add((step, day, u_idx, tuple(pos) if pos else None))
            elif crop == 'MELON':
                melon_tiles.add((step, day, u_idx, tuple(pos) if pos else None))

print(f"Total Tomato Plant Actions: {len(tomato_tiles)}")
for t in sorted(list(tomato_tiles))[:25]:
    print(f"Step {t[0]:3d} (Day {t[1]:2d}): Worker {t[2]} at {t[3]}")
