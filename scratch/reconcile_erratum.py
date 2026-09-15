import pandas as pd
import json

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
with open('experiments/EXP-DEV-004/RAW_RESULTS.json') as f:
    raw = json.load(f)
with open('experiments/EXP-DEV-004/STATISTICS_RECOMPUTED.json') as f:
    stats = json.load(f)

pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

print("=== RECONCILIATION AUDIT METRICS ===")
# 1. Total seeds
n_seeds = len(deltas)
print(f"Total seeds: {n_seeds}")

# 2. Wins, Losses, Ties
wins = (deltas['paired_mean_delta'] > 0).sum()
losses = (deltas['paired_mean_delta'] < 0).sum()
ties = (deltas['paired_mean_delta'] == 0).sum()
print(f"Wins: {wins}, Losses: {losses}, Ties: {ties}")

# 3. Activation derivations
# A. Seeds where cand0_plan != BASELINE_BACKBONE or cand1_plan != BASELINE_BACKBONE (Terminal activation recorded in PAIRED_DELTAS.csv)
terminal_act_seeds = deltas[deltas['activated'] == True]['seed'].tolist()
print(f"Terminal activation count (from PAIRED_DELTAS.csv): {len(terminal_act_seeds)} ({len(terminal_act_seeds)/n_seeds:.1%})")

# B. Seeds where selected_plan != 'BASELINE_BACKBONE' at ANY checkpoint in PLAN_EVENTS.csv
any_act_seeds = pe[pe['selected_plan'] != 'BASELINE_BACKBONE']['seed'].unique().tolist()
print(f"Any-step activation count (from PLAN_EVENTS.csv): {len(any_act_seeds)} ({len(any_act_seeds)/n_seeds:.1%})")

# C. Total plan-selection events in PLAN_EVENTS.csv
total_events = len(pe)
spec_events = (pe['decision'] == 'SPECIALIZE').sum()
base_events = (pe['decision'] == 'BASELINE').sum()
print(f"Total plan-selection events: {total_events} (Specialize: {spec_events}, Baseline: {base_events})")

# D. Route reversals (specialized -> baseline)
reversals = []
for s in sorted(pe['seed'].unique()):
    for m in [0, 1]:
        sub = pe[(pe['seed'] == s) & (pe['match'] == m)]
        plans = sub['selected_plan'].tolist()
        steps = sub['step'].tolist()
        for i in range(len(plans) - 1):
            if plans[i] != 'BASELINE_BACKBONE' and plans[i+1] == 'BASELINE_BACKBONE':
                reversals.append({
                    'seed': s, 'match': m, 'from_step': steps[i], 'to_step': steps[i+1],
                    'from_plan': plans[i], 'to_plan': plans[i+1]
                })

df_rev = pd.DataFrame(reversals)
print(f"Total route reversal events: {len(df_rev)}")
print(f"Total seeds with route reversal: {df_rev['seed'].nunique()}")
print("Reversals by step transition:")
print(df_rev.groupby(['from_step', 'to_step']).size())

# E. Cross-tabulate reversals with outcome
rev_seed_list = df_rev['seed'].unique().tolist()
deltas['has_reversal'] = deltas['seed'].isin(rev_seed_list)
print("\nOutcome by Reversal Status:")
print(pd.crosstab(deltas['has_reversal'], deltas['outcome']))

# F. Total economic impact of reversal seeds vs non-reversal seeds
print("\nMean delta by Reversal Status:")
print(deltas.groupby('has_reversal')['paired_mean_delta'].agg(['count', 'sum', 'mean', 'median']))

# G. Losses breakdown
print("\nLosses breakdown:")
losses_df = deltas[deltas['outcome'] == 'LOSS']
print(f"Total losses: {len(losses_df)}")
print(f"Losses with reversal: {losses_df['has_reversal'].sum()}")
print(f"Losses without reversal: {(~losses_df['has_reversal']).sum()}")
print("Loss seeds without reversal:", losses_df[~losses_df['has_reversal']]['seed'].tolist())
