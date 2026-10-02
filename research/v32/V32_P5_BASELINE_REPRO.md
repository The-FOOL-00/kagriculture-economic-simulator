# V32 P5 BASELINE REPRODUCTION REPORT (P4 Arm 1 Control)

Date: 2026-09-23.
Script: `scratch/v32_p5_verify_arm1.py`.
Target Checkpoint: `results/v32_p4_arm1_balanced.npz` (SHA16 `34587d45cd5ed4d9`).

## 1. Checkpoint Verification
- Architecture: `P3Policy` (157 dims $\to$ 3×256 Tanh MLP $\to$ native factorized heads; 277,092 params).
- Training metadata: `arm=arm1_balanced`, `epochs=30`, `lr=0.003`, `crit_weight=50.0`, `val_full_exact=0.053`.

## 2. Supervised Step-0 Wash Probe (G1 Replication)
Evaluated across all 240 step-0 samples in the dataset (192 train + 48 val):
- **Wash Shape Rate**: **240/240 (100.0%)**
- **Exact Literal Match**: **60/240 (25.0%)** (theoretical ceiling under mixture supervision)
- **Slot 0 Probability**: $P(\text{BUY\_PRODUCT}) = 0.938$, $P(\text{SELL}) = 0.062$
- **Slot 1 Probability**: $P(\text{BUY\_PRODUCT}) = 0.040$, $P(\text{SELL}) = 0.952$
- **Slot 0 Argmax**: `['BUY_PRODUCT', 'WHEAT', 30]`
- **Slot 1 Argmax**: `['SELL', 'WHEAT', 30]`
- **Slots 2–9 Argmax**: `[]` (NOOP)

## 3. Closed-Loop 120-Leg Screen (P4 Screen Seeds `249675–249684`)
Evaluated across 10 seeds × 6 opponents × 2 seats = 120 legs:
- **Mean Terminal Cash**: **$108.39**
- **Median Terminal Cash**: **$0.50**
- **Standard Deviation**: $309.98
- **Min / Max**: $0.00 / $2,246.00
- **Win Rate**: 0.0% (0/120)
- **Step-0 Wash Execution Rate**: **120/120 (100.0%)**

## 4. Verdict
The P4 Arm 1 baseline reproduces bit-for-bit with 100% opening wash fidelity and identical economic telemetry. Baseline reproduction is **PASSED**.
