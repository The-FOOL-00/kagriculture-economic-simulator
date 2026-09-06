import json

with open("scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps")
print("=== DAY 0 SETUP for GAYATHRI SALINI (P0) vs V2 (P1) ===")
for s in range(5):
    act0 = steps[s][0].get("action", {})
    act1 = steps[s][1].get("action", {})
    m0 = act0.get("market", [])
    m1 = act1.get("market", [])
    print(f"Step {s:2d} | P0(Gayathri): {act0.get('farmer')} | market: {m0}")
    print(f"        | P1(V2):       {act1.get('farmer')} | market: {m1}")
