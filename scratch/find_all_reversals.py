import pandas as pd

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

reversal_seeds = []
for seed in sorted(pe['seed'].unique()):
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0]['selected_plan'].tolist()
    d = deltas[deltas['seed'] == seed].iloc[0]
    
    # Check if there is any transition from non-baseline to baseline or vice versa
    transitions = []
    for i in range(len(m0_plans) - 1):
        if m0_plans[i] != m0_plans[i+1]:
            transitions.append((sub[sub['match'] == 0]['step'].iloc[i+1], m0_plans[i], m0_plans[i+1]))
    
    # Reversal specifically means abandoning a specialized route (specialized -> baseline)
    abandonments = [t for t in transitions if t[1] != 'BASELINE_BACKBONE' and t[2] == 'BASELINE_BACKBONE']
    if abandonments:
        reversal_seeds.append((seed, d['outcome'], d['paired_mean_delta'], m0_plans, transitions))

print(f"Total seeds with at least one route reversal (specialized -> baseline): {len(reversal_seeds)}")
for s, outcome, delta, plans, trans in reversal_seeds:
    print(f"Seed {s}: outcome={outcome:4s}, delta={delta:+8.1f}, plans={plans}, trans={trans}")
