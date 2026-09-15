import pandas as pd
import json

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

# Find seeds where cand0_plan == 'BASELINE_BACKBONE' but paired_mean_delta != 0
bb_nonzero = deltas[(deltas['cand0_plan'] == 'BASELINE_BACKBONE') & (deltas['paired_mean_delta'] != 0)]
print(f"Total seeds with cand0_plan == BASELINE_BACKBONE but nonzero delta: {len(bb_nonzero)}")
print(bb_nonzero[['seed', 'match0_cand_p0', 'match0_base_p1', 'match0_delta', 'match1_base_p0', 'match1_cand_p1', 'match1_delta', 'paired_mean_delta', 'outcome', 'activated']])

print("\nPlan events for these seeds:")
for seed in bb_nonzero['seed']:
    sub = pe[pe['seed'] == seed]
    m0_plans = sub[sub['match'] == 0][['step', 'selected_plan', 'decision', 'best_candidate_plan', 'best_candidate_delta', 'tau_hurdle']].to_dict('records')
    m1_plans = sub[sub['match'] == 1][['step', 'selected_plan', 'decision', 'best_candidate_plan', 'best_candidate_delta', 'tau_hurdle']].to_dict('records')
    print(f"\n--- Seed {seed} ---")
    print(f"Match 0 plan events:")
    for r in m0_plans:
        print(f"  Step {r['step']}: best={r['best_candidate_plan']} (delta={r['best_candidate_delta']:.1f}, tau={r['tau_hurdle']:.1f}) -> selected={r['selected_plan']} ({r['decision']})")
    print(f"Match 1 plan events:")
    for r in m1_plans:
        print(f"  Step {r['step']}: best={r['best_candidate_plan']} (delta={r['best_candidate_delta']:.1f}, tau={r['tau_hurdle']:.1f}) -> selected={r['selected_plan']} ({r['decision']})")
