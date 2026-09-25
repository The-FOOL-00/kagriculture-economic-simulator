import json
import os

files = [
    'tournament_dev_results.json',
    'tournament_fresh_results.json',
    'tournament_ablation_results.json'
]

for fname in files:
    fpath = os.path.join('scratch', 'v38', fname)
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
    print(f"\n==================== {fname} ====================")
    with open(fpath, 'r') as f:
        data = json.load(f)
    print(f"Elapsed: {data.get('elapsed_seconds', 0):.1f}s | Seeds: {data.get('seeds')} | Opponents: {data.get('opponents')}")
    summary = data.get('policy_summaries', {})
    for cand, stats in summary.items():
        pts = stats['points']
        wr = stats['win_rate']
        cash = stats['mean_cash']
        delta = stats['mean_paired_delta']
        worst = stats['worst_paired_delta']
        rescues = stats['rescues']
        casualties = stats['casualties']
        interventions = stats['mean_interventions']
        latency = stats['mean_latency_ms']
        print(f"  {cand:20s} | M: {stats['matches']:2d} | Pts: {pts:4.1f} | WR: {wr:5.1f}% | Cash: ${cash:9.1f} | PairedDelta: ${delta:+7.2f} | Worst: ${worst:+7.2f} | Rescues: {rescues} | Casualties: {casualties} | Interv: {interventions:.2f} | Latency: {latency:.2f}ms")

    # If raw results exist, let's inspect breakdown by opponent
    raw = data.get('raw_results', [])
    print(f"  Total raw match records: {len(raw)}")
