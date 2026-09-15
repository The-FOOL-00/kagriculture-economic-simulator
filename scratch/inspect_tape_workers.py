import json

with open('extracted_agents/dmitrii_lb2800/actions.json') as f:
    tapes = json.load(f)

for t_idx in [0, 6, 7]:
    tape = tapes[t_idx]
    print(f"\n--- TAPE {t_idx} ---")
    for day in range(30):
        step = day * 24 + 12 # midday
        hands = len(tape[step].get('hands', []))
        hires = sum(1 for s in range(day*24, (day+1)*24) for o in tape[s].get('market', []) if o and o[0] == 'HIRE')
        lands = [o for s in range(day*24, (day+1)*24) for o in tape[s].get('market', []) if o and o[0] == 'BUY_LAND']
        print(f"Day {day:2d} (Steps {day*24:3d}-{day*24+23:3d}): Hands={hands:2d} | Hires placed={hires:2d} | Lands={lands}")
