import json

with open('research/v57/counterfactuals/QUEUE_ALIGNMENT_MATRIX.json') as f:
    d = json.load(f)

for k, v in d.items():
    leg_str = ' | '.join([f"{leg}: delta={data['delta_vs_baseline']:+.1f} (marg={data['margin']:+.1f})" for leg, data in v['legs'].items()])
    print(f"{k:32s}: Mean={v['mean_delta']:>+7.1f} | {leg_str}")
