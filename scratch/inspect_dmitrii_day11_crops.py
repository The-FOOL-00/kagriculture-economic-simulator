import json

with open('extracted_agents/dmitrii_lb2800/actions.json') as f:
    tapes = json.load(f)

tape0 = tapes[0]

print("=== DMITRII TAPE 0: DAY 10 to 13 ACTIONS ===")
for step in range(240, 312):
    act = tape0[step]
    market = act.get('market', [])
    farmer = act.get('farmer', ['PASS'])
    hands = act.get('hands', [])
    plants = [w for w in [farmer] + hands if w and w[0] == 'PLANT']
    harvests = [w for w in [farmer] + hands if w and w[0] == 'HARVEST']
    waters = [w for w in [farmer] + hands if w and w[0] == 'WATER']
    sells = [o for o in market if o and o[0] == 'SELL']
    buys = [o for o in market if o and o[0].startswith('BUY')]
    if plants or harvests or sells or buys or step in [240, 264, 288]:
        day = step // 24
        hour = step % 24
        print(f"Step {step:3d} (D{day:2d}:H{hour:2d}): Sells={sells} | Buys={buys} | Harvests={len(harvests)} | Plants={plants}")
