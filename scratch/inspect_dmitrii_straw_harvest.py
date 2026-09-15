import json

with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
    tapes = json.load(f)

tape0 = tapes[0]

print("=== DMITRII TAPE 0: DAY 21 (STEPS 504 TO 527) ===")
for step in range(504, 528):
    hour = step % 24
    act = tape0[step]
    farmer = act.get("farmer", ["PASS"])
    hands = act.get("hands", [])
    units = [farmer] + hands
    
    harvests = [(i, u) for i, u in enumerate(units) if u and u[0] == "HARVEST"]
    waters = [(i, u) for i, u in enumerate(units) if u and u[0] == "WATER"]
    drops = [(i, u) for i, u in enumerate(units) if u and u[0] == "DROP"]
    pickups = [(i, u) for i, u in enumerate(units) if u and u[0] == "PICKUP"]
    
    print(f"Step {step} (H{hour:2d}): Harvests={len(harvests)} | Waters={len(waters)} | Drops={len(drops)} | Market={act.get('market')}")
