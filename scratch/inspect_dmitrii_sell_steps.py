import json

with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
    tapes = json.load(f)

tape0 = tapes[0]

print("=== TAPE 0 SELL TIMING AUDIT ===")
sells_by_item = {}
sells_by_mod4 = {0: 0, 1: 0, 2: 0, 3: 0}

for step, act in enumerate(tape0):
    for m in act.get("market", []):
        if m and m[0] == "SELL":
            item, qty = m[1], m[2]
            sells_by_item.setdefault(item, []).append((step, step % 4, qty))
            sells_by_mod4[step % 4] += qty

print("Total sold quantity by step % 4:")
for m4, q in sells_by_mod4.items():
    print(f"  step % 4 == {m4}: {q} units")

print("\nDetail for STRAWBERRY, MILK, WOOL, CARROT:")
for it in ["STRAWBERRY", "MILK", "WOOL", "CARROT"]:
    orders = sells_by_item.get(it, [])
    print(f"\n{it}: {len(orders)} sell orders, total {sum(o[2] for o in orders)} units")
    for o in orders[:10]:
        print(f"  Step {o[0]} (mod 4 = {o[1]}): SELL {o[2]} units")
