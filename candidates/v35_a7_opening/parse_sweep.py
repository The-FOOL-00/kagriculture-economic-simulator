import json

with open("opening_wash_sweep.json") as f:
    d = json.load(f)

summary = d["summary"]
print(f"Total configs evaluated: {len(summary)}")
print(f"{'Config':<10} | {'Wins':<6} | {'WinRate':<8} | {'MeanCash':<10} | {'PairedDelta':<12} | {'Rescued':<8} | {'Casualties':<10} | {'MinCashD1':<10}")
print("-" * 88)

sorted_items = sorted(
    summary.items(),
    key=lambda x: (x[1]["win_rate"], x[1]["mean_paired_delta"]),
    reverse=True,
)
for k, v in sorted_items:
    wr_pct = f"{v['win_rate']*100:.1f}%"
    mc = f"${v['mean_cash']:.1f}"
    pd = f"${v['mean_paired_delta']:+.2f}"
    min_c = f"${v['min_day1_min_cash']:.1f}"
    print(f"{k:<10} | {v['wins']:<6.1f} | {wr_pct:<8} | {mc:<10} | {pd:<12} | {v['rescued_losses']:<8} | {v['casualty_wins']:<10} | {min_c:<10}")
