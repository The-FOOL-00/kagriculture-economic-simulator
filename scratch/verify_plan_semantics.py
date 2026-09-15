import pandas as pd

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

print("Verifying the True Plan State for all 50 seeds:")
always_baseline_seeds = []
specialized_seeds = []

for seed in sorted(pe['seed'].unique()):
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    d = deltas[deltas['seed'] == seed].iloc[0]
    is_always_bb = all(p == 'BASELINE_BACKBONE' for p in m0_plans)
    if is_always_bb:
        always_baseline_seeds.append((seed, d['paired_mean_delta']))
    else:
        specialized_seeds.append((seed, d['paired_mean_delta'], m0_plans, d['cand0_plan']))

print(f"\n1. Seeds that were ALWAYS BASELINE_BACKBONE at all steps: {len(always_baseline_seeds)}")
for s, delta in always_baseline_seeds:
    print(f"  Seed {s}: delta = {delta}")

print(f"\nAre all always-baseline seeds exactly 0.00 delta? {all(delta == 0.0 for _, delta in always_baseline_seeds)}")

print(f"\n2. Seeds that had terminal plan BASELINE_BACKBONE in PAIRED_DELTAS.csv: {len(deltas[deltas['cand0_plan'] == 'BASELINE_BACKBONE'])}")
for _, row in deltas[deltas['cand0_plan'] == 'BASELINE_BACKBONE'].iterrows():
    s = row['seed']
    sub = pe[pe['seed'] == s]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    print(f"  Seed {s}: delta = {row['paired_mean_delta']:+8.1f} | outcome = {row['outcome']:4s} | plan_seq = {m0_plans}")
