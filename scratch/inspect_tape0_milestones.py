import json

with open('extracted_agents/dmitrii_lb2800/actions.json') as f:
    tapes = json.load(f)

tape0 = tapes[0]
for step in range(len(tape0)):
    act = tape0[step]
    hires = [o for o in act.get('market', []) if o and o[0] == 'HIRE']
    hands = len(act.get('hands', []))
    lands = [o for o in act.get('market', []) if o and o[0] == 'BUY_LAND']
    if hires or lands or (step % 24 == 0 and hands > 0):
        day = step // 24
        hour = step % 24
        print(f"Step {step:3d} (Day {day:2d}:{hour:2d}): Hires in market: {len(hires)} | Hands in act: {hands} | Lands: {lands}")
