import json

with open("opening_sensitivity.json") as f:
    d = json.load(f)

for var, vals in d.items():
    print(f"\n=== Variable: {var} ===")
    for val, stats in vals.items():
        wr_pct = f"{stats['win_rate']*100:.1f}%"
        pd = f"${stats['mean_paired_delta']:+.2f}"
        print(f"  Val {val:<4} | Wins: {stats['wins']:.1f}/{stats['matches']} ({wr_pct}) | PairedDelta: {pd:<10} | Rescued: {stats['rescued_losses']} | Casualties: {stats['casualty_wins']}")
