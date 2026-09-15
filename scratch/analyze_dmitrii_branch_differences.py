import json

with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
    tapes = json.load(f)

print(f"Total tapes: {len(tapes)}")
tape0 = tapes[0]

for plan_idx in [1, 2, 3, 5, 7, 10, 12]:
    tape = tapes[plan_idx]
    farmer_diffs = 0
    hands_diffs = 0
    market_diffs = 0
    
    crops_planted = {}
    animals_placed = {}
    hires = 0
    
    for s in range(144, 719):
        a0 = tape0[s]
        a1 = tape[s]
        
        if a0.get("farmer") != a1.get("farmer"):
            farmer_diffs += 1
        if a0.get("hands") != a1.get("hands"):
            hands_diffs += 1
        if a0.get("market") != a1.get("market"):
            market_diffs += 1
            
        # Analyze plan actions
        for m in a1.get("market", []):
            if m and m[0] == "HIRE": hires += 1
        units = [a1.get("farmer", [])] + a1.get("hands", [])
        for u in units:
            if not u: continue
            if u[0] == "PLANT" and len(u) > 1:
                crops_planted[u[1]] = crops_planted.get(u[1], 0) + 1
            elif u[0] == "PLACE" and len(u) > 1:
                animals_placed[u[1]] = animals_placed.get(u[1], 0) + 1

    print(f"\n--- PLAN {plan_idx} vs PLAN 0 (Steps 144..718) ---")
    print(f"Diffs: Farmer={farmer_diffs}, Hands={hands_diffs}, Market={market_diffs}")
    print(f"Total Hires in Plan {plan_idx}: {hires}")
    print(f"Crops Planted: {crops_planted}")
    print(f"Animals Placed: {animals_placed}")
