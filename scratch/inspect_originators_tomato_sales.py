import json

filepath = "replays/live_tournament/episode_107543042.json"
with open(filepath) as f:
    ep = json.load(f)

opp_seat = 1

print("=== ORIGINATORS TOMATO SELLS (EPISODE 107543042) ===")
for step, s in enumerate(ep['steps']):
    day = step // 24
    hour = step % 24
    act = s[opp_seat].get('action', {})
    if not act: continue
    
    for m in act.get('market', []):
        if not m: continue
        if m[0] == 'SELL' and len(m) > 1 and m[1] == 'TOMATO':
            price = s[opp_seat]['observation']['market']['prices'].get('TOMATO')
            print(f"Step {step:3d} (Day {day:2d}:H{hour:2d}, step%4={step%4}): SELL TOMATO {m[2]} units @ price ${price}")
