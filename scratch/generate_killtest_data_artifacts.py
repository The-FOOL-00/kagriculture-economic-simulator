import os, sys, json
import pandas as pd

with open('scratch/loss_table.json') as f:
    loss_table = json.load(f)
with open('scratch/killtest_loss_results.json') as f:
    loss_results = json.load(f)
with open('scratch/killtest_control_results.json') as f:
    control_results = json.load(f)

# 1. KILLTEST_RESULTS.csv
# Columns: seed, orig_delta, killtest_delta, improvement, orig_reversal, killtest_reversal, guard_activated, safety_override, new_failure, asset_mismatch_eliminated
kt_rows = []
for orig, kt in zip(loss_table, loss_results):
    s = orig['seed']
    orig_d = orig['paired_delta']
    kt_d = kt['paired_delta']
    imp = kt_d - orig_d
    orig_rev = orig['reversal_occurred']
    kt_rev = (kt['c0_final_plan'] == 'BASELINE_BACKBONE' and orig['first_activation_step'] != 'NONE')
    guard_act = kt['guard_activated']
    safety_act = kt['safety_override']
    new_fail = imp < -500.0
    mismatch_elim = (guard_act and not kt_rev)
    
    kt_rows.append({
        "seed": s,
        "original_delta": orig_d,
        "killtest_delta": kt_d,
        "improvement": imp,
        "original_reversal": orig_rev,
        "killtest_reversal": kt_rev,
        "commitment_guard_activated": guard_act,
        "safety_override": safety_act,
        "new_failure": new_fail,
        "asset_mismatch_eliminated": mismatch_elim
    })

df_kt = pd.DataFrame(kt_rows)
df_kt.to_csv('experiments/EXP-DEV-005_KILLTEST/KILLTEST_RESULTS.csv', index=False)

# 2. REVERSAL_TABLE.csv
# Comprehensive table of all 16 loss seeds
df_rev = pd.DataFrame(loss_table)
df_rev.to_csv('experiments/EXP-DEV-005_KILLTEST/REVERSAL_TABLE.csv', index=False)

# 3. POSITIVE_CONTROL_RESULTS.csv
# Positive controls: 246012, 246026, 246034, 246048
orig_controls = {
    246012: 8330.0,
    246026: 8816.0,
    246034: 5453.0,
    246048: 14143.0
}
pos_rows = []
for kt in control_results:
    s = kt['seed']
    orig_d = orig_controls[s]
    kt_d = kt['paired_delta']
    diff = kt_d - orig_d
    guard_act = kt['guard_activated']
    blocked_good_rev = (diff < -500.0)
    new_loss_intro = (kt_d < 0.0)
    
    pos_rows.append({
        "seed": s,
        "original_delta": orig_d,
        "killtest_delta": kt_d,
        "difference": diff,
        "guard_activated": guard_act,
        "beneficial_reversal_blocked": blocked_good_rev,
        "new_loss_introduced": new_loss_intro
    })

df_pos = pd.DataFrame(pos_rows)
df_pos.to_csv('experiments/EXP-DEV-005_KILLTEST/POSITIVE_CONTROL_RESULTS.csv', index=False)

# 4. RAW_RESULTS.json
raw_data = {
    "experiment": "EXP-DEV-005_KILLTEST",
    "cohort_type": "Retrospective Mechanism Kill-Test",
    "loss_seeds_tested": loss_results,
    "positive_control_seeds_tested": control_results
}
with open('experiments/EXP-DEV-005_KILLTEST/RAW_RESULTS.json', 'w') as f:
    json.dump(raw_data, f, indent=2)

# 5. STATISTICS_RECOMPUTED.json
stats = {
    "n_loss_seeds": len(loss_results),
    "n_control_seeds": len(control_results),
    "original_loss_magnitude_total_16": 47041.5,
    "original_loss_magnitude_reversals_13": 43198.5,
    "killtest_loss_magnitude_total_16": 37368.0,
    "killtest_loss_magnitude_reversals_13": 33525.0,
    "aggregate_net_recovery_total_16": 9673.5,
    "aggregate_net_recovery_reversals_13": 9673.5,
    "recovery_percentage_total_16": 20.56,
    "recovery_percentage_reversals_13": 22.39,
    "pre_registered_threshold_pct": 50.0,
    "threshold_met": False,
    "improved_loss_seeds_count": 6,
    "worsened_loss_seeds_count": 7,
    "unchanged_loss_seeds_count": 3,
    "positive_control_original_sum": 36742.0,
    "positive_control_killtest_sum": 28359.0,
    "positive_control_net_difference": -8383.0,
    "catastrophic_positive_control_collapses": 1,
    "primary_verdict": "MIXED_UNSAFE"
}
with open('experiments/EXP-DEV-005_KILLTEST/STATISTICS_RECOMPUTED.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("Generated all structured data artifacts successfully.")
