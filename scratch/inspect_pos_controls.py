import pandas as pd

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

for s in [246012, 246026, 246034, 246048]:
    sub = pe[(pe['seed'] == s) & (pe['match'] == 0)]
    print(f"\n=== Positive Control Seed {s} ===")
    for _, row in sub.iterrows():
        print(f"Step {row['step']:3d}: shops={row['unlocked_shops']} | cash={row['cash']:7.1f} | best={row['best_candidate_plan']} | delta={row['best_candidate_delta']:7.1f} | sel={row['selected_plan']}")
