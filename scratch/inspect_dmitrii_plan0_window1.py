import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tapes_path = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")
with open(tapes_path, encoding="utf-8") as f:
    tapes = json.load(f)

plan0 = tapes[0]

print("=== DMITRII PLAN 0: WINDOW 1 (STEPS 144..215, DAYS 6..8) ===")
for step in range(144, 216):
    act = plan0[step]
    market = act.get("market", [])
    farmer = act.get("farmer", ["PASS"])
    hands = act.get("hands", [])
    
    interesting = False
    if market:
        interesting = True
    for h in [farmer] + hands:
        if h and h[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST", "WATER"):
            interesting = True
            
    if interesting:
        print(f"Step {step} (Day {step//24}, Hour {step%24}):")
        if market:
            print(f"  Market: {market}")
        for i, h in enumerate([farmer] + hands):
            if h and h[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST"):
                name = "Farmer" if i == 0 else f"Hand {i}"
                print(f"  {name}: {h}")
