import json
import os

dmitrii_actions_path = "extracted_agents/dmitrii_lb2800/actions.json"
with open(dmitrii_actions_path) as f:
    tapes = json.load(f)

tape0 = tapes[0]

print("=== TAPE 0 ANALYSIS (Default Plan 0) ===")
seed_buys = []
plants = []
sells = []

for step, act in enumerate(tape0):
    day = step // 24
    hour = step % 24
    
    # Market buys/sells
    for m in act.get('market', []):
        if not m: continue
        op = m[0]
        if op == 'BUY_SEED':
            seed_buys.append((step, day, hour, m[1], m[2]))
        elif op == 'SELL':
            sells.append((step, day, hour, m[1], m[2]))
            
    # Unit plants
    units = [act.get('farmer', [])] + act.get('hands', [])
    for u_idx, u in enumerate(units):
        if not u: continue
        if u[0] == 'PLANT':
            plants.append((step, day, hour, u_idx, u[1] if len(u) > 1 else 'UNKNOWN'))

print(f"\nTotal SEED BUYS: {len(seed_buys)}")
for b in seed_buys[:20]:
    print(f"Step {b[0]} (Day {b[1]}, Hr {b[2]}): BUY_SEED {b[3]} qty {b[4]}")
if len(seed_buys) > 20:
    print(f"... and {len(seed_buys)-20} more seed buys")

print(f"\nTotal PLANTS: {len(plants)}")
plant_counts = {}
for p in plants:
    crop = p[4]
    plant_counts[crop] = plant_counts.get(crop, 0) + 1
print("Plants by crop:", plant_counts)

print("\nSample plant actions:")
for p in plants[:25]:
    print(f"Step {p[0]} (Day {p[1]}, Hr {p[2]}): Unit {p[3]} PLANT {p[4]}")

print(f"\nTotal SELLS: {len(sells)}")
sell_counts = {}
for s in sells:
    item = s[3]
    sell_counts[item] = sell_counts.get(item, 0) + s[4]
print("Sells by item:", sell_counts)
