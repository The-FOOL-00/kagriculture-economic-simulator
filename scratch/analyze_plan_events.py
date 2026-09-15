import pandas as pd

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

print("=== ALL 14 WINS ===")
wins = deltas[deltas['outcome'] == 'WIN']
for seed in wins['seed']:
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    d = wins[wins['seed'] == seed].iloc[0]
    has_reversal = False
    for i in range(len(m0_plans) - 1):
        if m0_plans[i] != 'BASELINE_BACKBONE' and m0_plans[i+1] == 'BASELINE_BACKBONE':
            has_reversal = True
    print(f"Seed {seed}: delta={d['paired_mean_delta']:+8.1f} | terminal={d['cand0_plan']:18s} | reversal={str(has_reversal):5s} | m0={m0_plans}")

print("\n=== ALL 16 LOSSES ===")
losses = deltas[deltas['outcome'] == 'LOSS']
for seed in losses['seed']:
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    d = losses[losses['seed'] == seed].iloc[0]
    has_reversal = False
    for i in range(len(m0_plans) - 1):
        if m0_plans[i] != 'BASELINE_BACKBONE' and m0_plans[i+1] == 'BASELINE_BACKBONE':
            has_reversal = True
    print(f"Seed {seed}: delta={d['paired_mean_delta']:+8.1f} | terminal={d['cand0_plan']:18s} | reversal={str(has_reversal):5s} | m0={m0_plans}")

print("\n=== ALL 20 TIES ===")
ties = deltas[deltas['outcome'] == 'TIE']
for seed in ties['seed']:
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    d = ties[ties['seed'] == seed].iloc[0]
    has_reversal = False
    for i in range(len(m0_plans) - 1):
        if m0_plans[i] != 'BASELINE_BACKBONE' and m0_plans[i+1] == 'BASELINE_BACKBONE':
            has_reversal = True
    print(f"Seed {seed}: delta={d['paired_mean_delta']:+8.1f} | terminal={d['cand0_plan']:18s} | reversal={str(has_reversal):5s} | m0={m0_plans}")
