import json
import hashlib
import os
import tarfile

def run_verification():
    print("==================================================")
    print("1. FACTORIAL DATA VERIFICATION")
    print("==================================================")
    with open('scratch/corrected_causal_factorial_results.json') as f:
        fac = json.load(f)

    print("Cells in factorial results:")
    for k, v in fac['cells'].items():
        wr = v.get('win_rate', 0) * 100
        mm = v.get('mean_margin', 0)
        w, l, t = v.get('wins'), v.get('losses'), v.get('ties')
        print(f"  {k:15s}: WR={wr:6.2f}%, Mean Margin=${mm:+8.2f} (W={w}, L={l}, T={t})")

    print("\nCausal decomposition in factorial results:")
    print(json.dumps(fac.get('causal_decomposition', {}), indent=2))

    print("\n==================================================")
    print("2. HOLDOUT DATA VERIFICATION")
    print("==================================================")
    with open('scratch/corrected_holdout_and_gate_results.json') as f:
        hold = json.load(f)

    h_data = hold['holdout_vs_anchor']
    for k, v in h_data.items():
        if isinstance(v, (int, float, str, bool)):
            print(f"  {k:25s}: {v}")

    print("\n==================================================")
    print("3. FINAL RELEASE AUDIT VERIFICATION")
    print("==================================================")
    with open('scratch/final_release_audit.json') as f:
        rel = json.load(f)

    print("Interaction analysis:")
    print(json.dumps(rel.get('interaction_analysis', {}), indent=2))

    print("\nRuntime reconciliation:")
    print(json.dumps(rel.get('runtime_reconciliation', {}), indent=2))

if __name__ == '__main__':
    run_verification()
