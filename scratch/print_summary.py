import json

with open('scratch/full_forensic_suite_results.json') as f:
    full = json.load(f)
with open('scratch/meta_opponents_results.json') as f:
    meta = json.load(f)

for section, data in full.items():
    print(f"\n=== {section.upper()} ===")
    if isinstance(data, dict) and 'matches' in data:
        print(f"Matches: {data['matches']}, Cand Wins: {data['cand_wins']}")
        print(f"Pooled WR: {data['pooled_wr']*100:.2f}%, CI95: [{data['ci_95'][0]*100:.2f}%, {data['ci_95'][1]*100:.2f}%]")
        print(f"P0 WR: {data['p0_wr']*100:.2f}%, P1 WR: {data['p1_wr']*100:.2f}%")
        print(f"Mean Cand Cash: ${data['mean_cand_cash']:,.2f}, Mean Opp Cash: ${data['mean_opp_cash']:,.2f}, Margin: ${data['mean_margin']:,.2f}")
    elif isinstance(data, dict):
        for subk in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else x):
            subv = data[subk]
            print(f"  [{subk:25s}]: Matches={subv['matches']:3d}, Wins={subv['cand_wins']:3d}, WR={subv['pooled_wr']*100:5.1f}%, CI=[{subv['ci_95'][0]*100:4.1f}%, {subv['ci_95'][1]*100:4.1f}%], Margin=+${subv['mean_margin']:6,.1f}, CandCash=${subv['mean_cand_cash']:6,.1f}, OppCash=${subv['mean_opp_cash']:6,.1f}")

print("\n=== META OPPONENTS ===")
for k in sorted(meta.keys()):
    v = meta[k]
    print(f"  [{k:30s}]: Matches={v['matches']:3d}, Wins={v['cand_wins']:3d}, WR={v['pooled_wr']*100:5.1f}%, CI=[{v['ci_95'][0]*100:4.1f}%, {v['ci_95'][1]*100:4.1f}%], Margin=+${v['mean_margin']:6,.1f}, CandCash=${v['mean_cand_cash']:6,.1f}, OppCash=${v['mean_opp_cash']:6,.1f}")
