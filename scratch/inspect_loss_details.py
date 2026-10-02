import json

data = json.load(open("research/v56/analysis/V49_FOUR_LOSSES.json"))
for lid, l in data["four_losses"].items():
    print(f"=== {lid}: Seed {l['seed']} Seat {l['seat']} Margin: ${l['margin']:+.2f} ===")
    print(f"  V49 Final: ${l['v49_final_cash']:.2f} | V44 Final: ${l['v44_final_cash']:.2f}")
    print(f"  V49 animals: {l['v49_terminal_animals']}")
    print(f"  V44 animals: {l['v44_terminal_animals']}")
    print(f"  V49 terminal shed: {l['v49_terminal_shed']}")
    print(f"  V44 terminal shed: {l['v44_terminal_shed']}")
    print(f"  Shops: {l['terminal_shops']}")
    print("  V49 revenue by commodity:")
    for k, v in l["v49_commodity_revenue"].items():
        print(f"    {k:<12}: qty = {v['qty']:>4}, rev = ${v['revenue']:>9.2f}, avg = ${v['avg_price']:>6.2f}")
    print("  V44 revenue by commodity:")
    for k, v in l["v44_commodity_revenue"].items():
        print(f"    {k:<12}: qty = {v['qty']:>4}, rev = ${v['revenue']:>9.2f}, avg = ${v['avg_price']:>6.2f}")
    print()

print("=== COMPARISON WINS ===")
for wid, w in data["comparison_wins"].items():
    print(f"=== {wid}: Seed {w['seed']} Margin: ${w['margin']:+.2f} ===")
    print(f"  V49 Final: ${w['v49_final_cash']:.2f} | V44 Final: ${w['v44_final_cash']:.2f}")
    print(f"  Shops: {w['terminal_shops']}")
    print(f"  V49 animals: {w['v49_terminal_animals']}")
    print(f"  V44 animals: {w['v44_terminal_animals']}")
