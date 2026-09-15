import json

with open('scratch/crop_portfolio_sweep_results.json', 'r') as f:
    data = json.load(f)

print(f"{'Allocation':12s} {'Mean Cash':>11s} {'Margin':>10s} {'Win Rate':>10s} {'Worst Loss':>12s} {'Downside Risk':>14s}")
print("-" * 75)
for r in data:
    print(f"{r['allocation']:12s} {r['mean_cash']:>11.2f} {r['mean_margin']:>+10.2f} {r['win_rate']*100:>9.1f}% {r['worst_loss']:>+12.2f} {r['downside_risk']:>14.2f}")
