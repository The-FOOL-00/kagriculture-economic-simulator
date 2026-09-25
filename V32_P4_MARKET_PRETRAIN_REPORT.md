# V32 P4 MARKET PRETRAIN REPORT (Arm 2)

Date: 2026-09-23.
Script: `scripts/v32_p4_train.py --arm arm2_mkt_pretrain --epochs 30 --lr 3e-3 --crit-weight 50.0`.
Artifacts:
- Checkpoint: `results/v32_p4_arm2_mkt_pretrain.npz`
- Report: `results/v32_p4_arm2_report.json`

## 1. Objective
Test the first half of Hypothesis H2:
Can a dedicated market pretraining phase on the full 138k dataset learn the critical market behavior (step-0 opening wash + general non-NOOP market actions + slot ordering) before any unit-head optimization?

## 2. Training Protocol (§17)
- Model: Native factorized `P3Policy` (277k params).
- Features: 157-dim temporal features (frozen normalizer).
- Objective: $L_{mkt} + \lambda_{crit} L_{crit}$ (market heads + trunk active; unit heads receive 0 gradient).
- Epochs: 30 epochs (Adam lr=3e-3, batch=1024).

## 3. Results

### 3.1 Market Head Fidelity
- Validation `market_op`: **0.973** (97.3%).
- Validation `market_op_nonnoop`: **0.825** (82.5%).
- Step-0 Wash Shape Recovery: **240/240 (100.0%)** across ALL 30 epochs.
- Step-0 Exact Literal Match: **60/240 (25.0%)** (theoretical ceiling).
- Step-0 Slot 0 Probabilities: $P(\text{BUY\_PRODUCT}) = 0.92$, $P(\text{SELL}) = 0.08$.
- Step-0 Slot 1 Probabilities: $P(\text{SELL}) = 0.92$, $P(\text{BUY\_PRODUCT}) = 0.05$.
- Predicted Step-0 Market Action:
  - Slot 0: `['BUY_PRODUCT', 'WHEAT', 30]` (or 7–50)
  - Slot 1: `['SELL', 'WHEAT', 30]` (or 2–50)
  - Slots 2–9: `[]` (NOOP)

### 3.2 Unit Heads (Untrained Control)
- `farmer_op`: 0.056 (random baseline).
- `unit_op`: 0.072 (random baseline).
- `val_full_exact`: 0.004.
As expected, unit parameters remained untrained.

## 4. Verification Check (§17 Gate)
The pretrained market model satisfies all three preregistered criteria:
1. Reproduces the step-0 wash (240/240).
2. Reproduces general non-NOOP market actions (0.825).
3. Preserves race-aligned slot ordering (`[BUY, SELL]`).

The checkpoint is verified and ready for attachment to the full policy in Arm 3 (frozen) and Arm 4 (unfrozen).
